from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]+")
WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
PUNCT_RE = re.compile(r"[\s\t\r\n、。．，・：:；;（）()［］\[\]{}『』「」\"'`]+")

DOMAIN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "申請": ("手続き", "申し込み", "申込み", "申請書", "届け出"),
    "必要書類": ("持ち物", "必要なもの", "提出書類", "書類", "本人確認書類"),
    "子ども": ("こども", "児童", "子供"),
    "医療費": ("医療", "助成", "受給資格"),
    "ごみ": ("ゴミ", "粗大ごみ", "廃棄", "収集"),
    "体育館": ("スポーツ施設", "施設", "利用", "予約"),
    "住民票": ("証明書", "住民票の写し", "交付"),
    "転入": ("引っ越し", "引越し", "住所変更", "届出"),
}

STOP_TOKENS = {
    "について", "ください", "できます", "したい", "知りたい", "教えて",
    "です", "ます", "こと", "もの", "どこ", "いつ", "なに", "何",
}


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    body: str
    source: str
    metadata: dict[str, str]

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}".strip()


@dataclass(frozen=True)
class SearchHit:
    doc: SourceDocument
    score: float
    matched_terms: tuple[str, ...]

    @property
    def confidence(self) -> str:
        if self.score >= 9:
            return "high"
        if self.score >= 4:
            return "medium"
        return "low"


def normalize_text(text: str) -> str:
    text = text.casefold().replace("　", " ")
    text = PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _ngrams(s: str, n: int) -> set[str]:
    compact = re.sub(r"\s+", "", s)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def tokenize(text: str) -> set[str]:
    normalized = normalize_text(text)
    tokens: set[str] = set()

    for word in WORD_RE.findall(normalized):
        if len(word) >= 2 and word not in STOP_TOKENS:
            tokens.add(word)

    for seq in CJK_RE.findall(normalized):
        for term, synonyms in DOMAIN_SYNONYMS.items():
            if term in seq:
                tokens.add(term)
            for synonym in synonyms:
                if synonym.casefold() in seq:
                    tokens.add(synonym.casefold())
        tokens.update(token for token in _ngrams(seq, 2) if token and token not in STOP_TOKENS)
        tokens.update(token for token in _ngrams(seq, 3) if token and token not in STOP_TOKENS)

    expanded = set(tokens)
    for term, synonyms in DOMAIN_SYNONYMS.items():
        term_cf = term.casefold()
        synonym_set = {s.casefold() for s in synonyms}
        if term_cf in tokens or tokens.intersection(synonym_set):
            expanded.add(term_cf)
            expanded.update(synonym_set)
    return expanded


def parse_markdown_corpus(text: str, *, source: str = "inline") -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    current_title: str | None = None
    current_lines: list[str] = []
    current_id = ""
    top_title = ""

    def flush() -> None:
        nonlocal current_title, current_lines, current_id
        if not current_title:
            return
        body = "\n".join(current_lines).strip()
        if not body:
            return
        metadata: dict[str, str] = {}
        content_lines: list[str] = []
        for line in body.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key in {"カテゴリ", "対象", "担当課", "最終確認日", "受付窓口", "注意"} and value:
                    metadata[key] = value
            content_lines.append(line)
        doc_no = len(docs) + 1
        doc_id = current_id or f"{Path(source).stem.upper()}-{doc_no:03d}"
        docs.append(SourceDocument(doc_id, current_title, "\n".join(content_lines).strip(), source, metadata))

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                top_title = title
                continue
            if level in {2, 3}:
                flush()
                current_title = title
                current_lines = []
                id_match = re.search(r"\b([A-Z]{2,}-\d{3,})\b", title)
                current_id = id_match.group(1) if id_match else ""
                if top_title:
                    current_lines.append(f"コーパス: {top_title}")
                continue
        if current_title:
            current_lines.append(line)
    flush()
    return docs


def chunk_plain_text(text: str, *, source: str = "inline", max_chars: int = 900) -> list[SourceDocument]:
    cleaned = text.strip()
    if not cleaned:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n---\n", cleaned) if p.strip()]
    docs: list[SourceDocument] = []
    for idx, paragraph in enumerate(paragraphs, start=1):
        while len(paragraph) > max_chars:
            head, paragraph = paragraph[:max_chars], paragraph[max_chars:]
            docs.append(SourceDocument(f"{Path(source).stem.upper()}-{len(docs)+1:03d}", f"参照文書 {idx}", head.strip(), source, {}))
        docs.append(SourceDocument(f"{Path(source).stem.upper()}-{len(docs)+1:03d}", f"参照文書 {idx}", paragraph.strip(), source, {}))
    return docs


def load_corpus_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_documents(corpora: list[tuple[str, str]]) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for source, text in corpora:
        if not text.strip():
            continue
        parsed = parse_markdown_corpus(text, source=source)
        docs.extend(parsed if parsed else chunk_plain_text(text, source=source))
    return docs


def _idf(doc_count: int, containing_count: int) -> float:
    return math.log((doc_count + 1) / (containing_count + 1)) + 1.0


def search(question: str, docs: list[SourceDocument], *, limit: int = 4) -> list[SearchHit]:
    query_tokens = tokenize(question)
    if not question.strip() or not docs or not query_tokens:
        return []

    doc_tokens = {doc.id: tokenize(doc.text) for doc in docs}
    document_frequency: dict[str, int] = {}
    for tokens in doc_tokens.values():
        for token in tokens:
            document_frequency[token] = document_frequency.get(token, 0) + 1

    hits: list[SearchHit] = []
    normalized_question = normalize_text(question)
    for doc in docs:
        tokens = doc_tokens[doc.id]
        matched = sorted(query_tokens.intersection(tokens))
        if not matched:
            continue
        score = 0.0
        for token in matched:
            weight = _idf(len(docs), document_frequency.get(token, 1))
            if len(token) >= 3:
                weight *= 1.25
            if token in DOMAIN_SYNONYMS or any(token in v for v in DOMAIN_SYNONYMS.values()):
                weight *= 1.35
            score += weight

        normalized_doc = normalize_text(doc.text)
        for phrase in re.findall(r"[\u3040-\u30ff\u3400-\u9fff]{4,}|[a-zA-Z0-9_]{4,}", normalized_question):
            if phrase in normalized_doc:
                score += 2.0
        if any(word in question for word in ["必要", "書類", "持ち物"]) and any(word in doc.text for word in ["必要なもの", "必要書類", "持ち物", "提出書類"]):
            score += 2.5
        if any(word in question for word in ["いつ", "期限", "期間"]) and any(word in doc.text for word in ["受付期間", "期限", "期間", "いつ"]):
            score += 1.5
        if any(word in question for word in ["どこ", "窓口", "場所"]) and any(word in doc.text for word in ["受付窓口", "窓口", "場所"]):
            score += 1.5
        if score > 0:
            hits.append(SearchHit(doc, round(score, 3), tuple(matched[:12])))
    hits.sort(key=lambda hit: (hit.score, hit.doc.id), reverse=True)
    return hits[: max(1, limit)]


def is_answerable(hits: list[SearchHit], *, threshold: float = 4.0) -> bool:
    if not hits:
        return False
    best = hits[0]
    if best.score >= threshold:
        return True
    return len(hits) >= 2 and best.score >= 3.0 and hits[1].score >= 2.0


def excerpt(text: str, *, max_chars: int = 360) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"
