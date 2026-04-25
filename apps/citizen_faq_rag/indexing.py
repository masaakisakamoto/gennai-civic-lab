from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .retriever import SearchHit, SourceDocument, build_documents, load_corpus_text, tokenize

INDEX_SCHEMA_VERSION = "gennai.faq_bm25_index.v1"
DEFAULT_INDEX_PATH = Path(".gennai/index/citizen_faq_bm25.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def document_to_dict(doc: SourceDocument) -> dict[str, Any]:
    return {
        "id": doc.id,
        "title": doc.title,
        "body": doc.body,
        "source": doc.source,
        "metadata": dict(doc.metadata),
    }


def document_from_dict(data: dict[str, Any]) -> SourceDocument:
    return SourceDocument(
        id=str(data.get("id", "")),
        title=str(data.get("title", "")),
        body=str(data.get("body", "")),
        source=str(data.get("source", "")),
        metadata={str(k): str(v) for k, v in dict(data.get("metadata", {})).items()},
    )


def fingerprint_documents(docs: list[SourceDocument]) -> str:
    """Return a stable corpus fingerprint for versioning and stale-index detection."""

    payload = [document_to_dict(doc) for doc in docs]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass(frozen=True)
class CorpusVersion:
    schema_version: str
    corpus_id: str
    corpus_fingerprint: str
    document_count: int
    sources: list[str]
    built_at: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PersistentBM25Index:
    schema_version: str
    corpus_version: CorpusVersion
    documents: list[SourceDocument]
    term_counts: dict[str, dict[str, int]]
    doc_lengths: dict[str, int]
    doc_freq: dict[str, int]
    avg_doc_length: float
    k1: float = 1.4
    b: float = 0.75

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "corpus_version": self.corpus_version.to_dict(),
            "documents": [document_to_dict(doc) for doc in self.documents],
            "term_counts": self.term_counts,
            "doc_lengths": self.doc_lengths,
            "doc_freq": self.doc_freq,
            "avg_doc_length": self.avg_doc_length,
            "k1": self.k1,
            "b": self.b,
        }


def build_corpus_version(docs: list[SourceDocument], *, corpus_id: str = "citizen_faq") -> CorpusVersion:
    sources = sorted({doc.source for doc in docs})
    return CorpusVersion(
        schema_version="gennai.corpus_version.v1",
        corpus_id=corpus_id,
        corpus_fingerprint=fingerprint_documents(docs),
        document_count=len(docs),
        sources=sources,
        built_at=utc_now(),
        notes=[
            "Generated from local corpus text.",
            "Do not commit indexes built from confidential or personal data.",
        ],
    )


def build_persistent_bm25_index(
    docs: list[SourceDocument],
    *,
    corpus_id: str = "citizen_faq",
    k1: float = 1.4,
    b: float = 0.75,
) -> PersistentBM25Index:
    term_counts: dict[str, dict[str, int]] = {}
    doc_lengths: dict[str, int] = {}
    doc_freq: dict[str, int] = {}

    for doc in docs:
        counts: Counter[str] = Counter(tokenize(doc.text))
        term_counts[doc.id] = dict(counts)
        doc_lengths[doc.id] = sum(counts.values()) or 1
        for term in counts:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    avg_len = sum(doc_lengths.values()) / max(1, len(doc_lengths))
    return PersistentBM25Index(
        schema_version=INDEX_SCHEMA_VERSION,
        corpus_version=build_corpus_version(docs, corpus_id=corpus_id),
        documents=docs,
        term_counts=term_counts,
        doc_lengths=doc_lengths,
        doc_freq=doc_freq,
        avg_doc_length=avg_len,
        k1=k1,
        b=b,
    )


def save_index(index: PersistentBM25Index, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def load_index(path: str | Path) -> PersistentBM25Index:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    corpus_data = data["corpus_version"]
    corpus_version = CorpusVersion(
        schema_version=str(corpus_data.get("schema_version", "")),
        corpus_id=str(corpus_data.get("corpus_id", "")),
        corpus_fingerprint=str(corpus_data.get("corpus_fingerprint", "")),
        document_count=int(corpus_data.get("document_count", 0)),
        sources=[str(x) for x in corpus_data.get("sources", [])],
        built_at=str(corpus_data.get("built_at", "")),
        notes=[str(x) for x in corpus_data.get("notes", [])],
    )
    return PersistentBM25Index(
        schema_version=str(data.get("schema_version", "")),
        corpus_version=corpus_version,
        documents=[document_from_dict(item) for item in data.get("documents", [])],
        term_counts={str(k): {str(t): int(v) for t, v in dict(value).items()} for k, value in data.get("term_counts", {}).items()},
        doc_lengths={str(k): int(v) for k, v in data.get("doc_lengths", {}).items()},
        doc_freq={str(k): int(v) for k, v in data.get("doc_freq", {}).items()},
        avg_doc_length=float(data.get("avg_doc_length", 1.0) or 1.0),
        k1=float(data.get("k1", 1.4)),
        b=float(data.get("b", 0.75)),
    )


def is_index_current(index: PersistentBM25Index, docs: list[SourceDocument]) -> bool:
    return index.corpus_version.corpus_fingerprint == fingerprint_documents(docs)


def search_index(index: PersistentBM25Index, question: str, *, limit: int = 4) -> list[SearchHit]:
    query_terms = list(tokenize(question))
    if not query_terms or not index.documents:
        return []

    hits: list[SearchHit] = []
    for doc in index.documents:
        counts = index.term_counts.get(doc.id, {})
        matched = sorted(set(query_terms).intersection(counts))
        if not matched:
            continue

        doc_len = index.doc_lengths.get(doc.id, 1) or 1
        length_norm = doc_len / (index.avg_doc_length or 1.0)
        score = 0.0
        for term in matched:
            tf = counts.get(term, 0)
            df = index.doc_freq.get(term, 0)
            idf = math.log(1 + (len(index.documents) - df + 0.5) / (df + 0.5))
            denominator = tf + index.k1 * (1 - index.b + index.b * length_norm)
            score += idf * ((tf * (index.k1 + 1)) / denominator)

        if score > 0:
            hits.append(SearchHit(doc, round(score * 8, 3), tuple(matched[:12])))

    hits.sort(key=lambda hit: (hit.score, hit.doc.id), reverse=True)
    return hits[: max(1, limit)]


def build_index_from_corpus_files(paths: list[Path], *, corpus_id: str = "citizen_faq") -> PersistentBM25Index:
    corpora = [(path.name, load_corpus_text(path)) for path in paths]
    return build_persistent_bm25_index(build_documents(corpora), corpus_id=corpus_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a persistent BM25 index for citizen_faq_rag")
    parser.add_argument("--corpus", nargs="+", required=True, help="Markdown/text corpus file(s)")
    parser.add_argument("--output", default=str(DEFAULT_INDEX_PATH), help="Output JSON index path")
    parser.add_argument("--corpus-id", default="citizen_faq", help="Stable corpus id for versioning")
    args = parser.parse_args(argv)

    paths = [Path(item) for item in args.corpus]
    index = build_index_from_corpus_files(paths, corpus_id=args.corpus_id)
    save_index(index, args.output)
    print(
        json.dumps(
            {
                "output": args.output,
                "schema_version": index.schema_version,
                "corpus_fingerprint": index.corpus_version.corpus_fingerprint,
                "document_count": index.corpus_version.document_count,
                "sources": index.corpus_version.sources,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
