from __future__ import annotations

import math
import os
from collections import Counter
from pathlib import Path
from dataclasses import dataclass
from typing import Protocol

from .retriever import SearchHit, SourceDocument, search as lexical_search, tokenize
from .indexing import DEFAULT_INDEX_PATH, is_index_current, load_index, search_index



def _doc_id(doc: SourceDocument | object) -> str:
    return str(getattr(doc, "id", doc))


def _doc_text(doc: SourceDocument | object) -> str:
    return str(getattr(doc, "text", doc))

class SearchBackend(Protocol):
    name: str

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        ...


@dataclass(frozen=True)
class LexicalSearchBackend:
    name: str = "lexical"

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        return lexical_search(question, docs, limit=limit)


@dataclass(frozen=True)
class BM25SearchBackend:
    """Small, dependency-free BM25 backend.

    This is not intended to beat a production search engine. Its job is to make the RAG app
    backend-pluggable while keeping local demos deterministic and API-key free.
    """

    name: str = "bm25"
    k1: float = 1.4
    b: float = 0.75

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        query_terms = list(tokenize(question))
        if not query_terms or not docs:
            return []

        doc_term_counts: dict[str, Counter[str]] = {}
        doc_lengths: dict[str, int] = {}
        for source_doc in docs:
            doc_id = _doc_id(source_doc)
            counts: Counter[str] = Counter(tokenize(_doc_text(source_doc)))
            doc_term_counts[doc_id] = counts
            doc_lengths[doc_id] = sum(counts.values()) or 1

        avg_len = sum(doc_lengths.values()) / max(1, len(doc_lengths))

        doc_freq: dict[str, int] = {}
        for counts in doc_term_counts.values():
            for term in counts:
                doc_freq[term] = doc_freq.get(term, 0) + 1

        hits: list[SearchHit] = []
        for source_doc in docs:
            doc_id = _doc_id(source_doc)
            counts = doc_term_counts[doc_id]
            matched = sorted(set(query_terms).intersection(counts))
            if not matched:
                continue

            score = 0.0
            for term in matched:
                tf = counts[term]
                df = doc_freq.get(term, 0)
                idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
                length_norm = doc_lengths[doc_id] / avg_len
                denominator = tf + self.k1 * (1 - self.b + self.b * length_norm)
                score += idf * ((tf * (self.k1 + 1)) / denominator)

            if score > 0:
                # Scale for the existing answerability thresholds.
                hits.append(SearchHit(source_doc, round(score * 8, 3), tuple(matched[:12])))

        hits.sort(key=lambda hit: (hit.score, _doc_id(hit.doc)), reverse=True)
        return hits[: max(1, limit)]


@dataclass(frozen=True)
class HybridSearchBackend:
    name: str = "hybrid"

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        lexical = LexicalSearchBackend().search(question, docs, limit=max(limit, 6))
        bm25 = BM25SearchBackend().search(question, docs, limit=max(limit, 6))

        by_doc: dict[str, SearchHit] = {}
        scores: dict[str, float] = {}
        matched: dict[str, set[str]] = {}

        def add(hits: list[SearchHit], weight: float) -> None:
            max_score = max((hit.score for hit in hits), default=1.0) or 1.0
            for hit in hits:
                by_doc[hit.doc.id] = hit
                scores[hit.doc.id] = scores.get(hit.doc.id, 0.0) + weight * (hit.score / max_score)
                matched.setdefault(hit.doc.id, set()).update(hit.matched_terms)

        add(lexical, 0.55)
        add(bm25, 0.45)

        combined: list[SearchHit] = []
        for doc_id, score in scores.items():
            base = by_doc[doc_id]
            combined.append(SearchHit(base.doc, round(score * 12, 3), tuple(sorted(matched[doc_id])[:12])))
        combined.sort(key=lambda hit: (hit.score, _doc_id(hit.doc)), reverse=True)
        return combined[: max(1, limit)]


@dataclass(frozen=True)
class PersistentBM25SearchBackend:
    """BM25 backend backed by a persisted JSON index when available.

    The backend falls back to in-memory BM25 if no index exists or if the index
    fingerprint does not match the current corpus. This keeps local demos robust
    while giving production-like workflows a deterministic index artifact.
    """

    name: str = "persistent_bm25"
    index_path: str | None = None

    def _path(self) -> Path:
        configured = self.index_path or os.environ.get("GENNAI_FAQ_INDEX_PATH")
        return Path(configured) if configured else DEFAULT_INDEX_PATH

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        path = self._path()
        if path.exists():
            try:
                index = load_index(path)
                if is_index_current(index, docs):
                    return search_index(index, question, limit=limit)
            except Exception:
                # The app must remain useful even if a local index is stale or malformed.
                pass
        return BM25SearchBackend(name="persistent_bm25:fallback").search(question, docs, limit=limit)


@dataclass(frozen=True)
class PersistentHybridSearchBackend:
    name: str = "hybrid_persistent"

    def search(self, question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
        lexical = LexicalSearchBackend().search(question, docs, limit=max(limit, 6))
        persistent = PersistentBM25SearchBackend().search(question, docs, limit=max(limit, 6))

        by_doc: dict[str, SearchHit] = {}
        scores: dict[str, float] = {}
        matched: dict[str, set[str]] = {}

        def add(hits: list[SearchHit], weight: float) -> None:
            max_score = max((hit.score for hit in hits), default=1.0) or 1.0
            for hit in hits:
                by_doc[hit.doc.id] = hit
                scores[hit.doc.id] = scores.get(hit.doc.id, 0.0) + weight * (hit.score / max_score)
                matched.setdefault(hit.doc.id, set()).update(hit.matched_terms)

        add(lexical, 0.5)
        add(persistent, 0.5)

        combined: list[SearchHit] = []
        for doc_id, score in scores.items():
            base = by_doc[doc_id]
            combined.append(SearchHit(base.doc, round(score * 12, 3), tuple(sorted(matched[doc_id])[:12])))
        combined.sort(key=lambda hit: (hit.score, _doc_id(hit.doc)), reverse=True)
        return combined[: max(1, limit)]


def get_search_backend(name: str | None) -> SearchBackend:
    normalized = (name or "lexical").strip().casefold()
    if normalized == "bm25":
        return BM25SearchBackend()
    if normalized == "hybrid":
        return HybridSearchBackend()
    if normalized in {"persistent_bm25", "indexed_bm25"}:
        return PersistentBM25SearchBackend()
    if normalized in {"hybrid_persistent", "persistent_hybrid"}:
        return PersistentHybridSearchBackend()
    return LexicalSearchBackend()
