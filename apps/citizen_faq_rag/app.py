from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None

from gennai_observability import add_observability_routes, observe_call

from gennai_app_kit import (
    GennaiPayloadError,
    GennaiValidationError,
    detect_prompt_injection,
    error_output,
    get_choice,
    get_inputs,
    get_str,
    markdown_report,
    normalize_files,
    output,
    redact_pii_with_counts,
    require_text,
)

from .retriever import SearchHit, build_documents, excerpt, is_answerable, load_corpus_text
from .search_backends import get_search_backend

APP_VERSION = "0.6.0"
SAMPLE_CORPUS = Path(__file__).resolve().parent / "corpus" / "sample_faq.md"

GENERIC_MATCH_FRAGMENTS = (
    "申請", "手続", "必要", "書類", "持ち物", "本人確認", "窓口",
    "教え", "ください", "でき", "ます", "です", "もの",
)


def _as_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _collect_corpora(inputs: dict[str, Any]) -> list[tuple[str, str]]:
    corpora: list[tuple[str, str]] = []
    use_sample = get_choice(inputs, "use_sample_corpus", allowed=["yes", "no"], default="yes")
    if use_sample == "yes":
        corpora.append(("sample_faq.md", load_corpus_text(SAMPLE_CORPUS)))

    documents = get_str(inputs, "documents", default="", max_chars=80_000)
    if documents:
        corpora.append(("inline_documents", documents))

    for file in normalize_files(inputs):
        corpora.append((file.filename or file.key, file.text()))
    return corpora


def _has_discriminative_match(hit: SearchHit) -> bool:
    title_and_meta = " ".join([hit.doc.title, *hit.doc.metadata.values()])
    for term in hit.matched_terms:
        if len(term) < 3:
            continue
        if any(fragment in term for fragment in GENERIC_MATCH_FRAGMENTS):
            continue
        # Require a discriminative term to appear in the title/metadata, not only in a body
        # fragment. This prevents questions like "パスポート申請" from matching unrelated
        # generic sections that merely contain "申請" or "必要なもの".
        if term in title_and_meta:
            return True
    return False


def _grounded_enough(hits: list[SearchHit]) -> bool:
    return bool(hits) and is_answerable(hits) and _has_discriminative_match(hits[0])


def _extract_relevant_lines(question: str, hit: SearchHit) -> list[str]:
    body = hit.doc.body
    lines = [line.rstrip() for line in body.splitlines()]
    lower_question = question.casefold()

    section_triggers: list[str] = []
    if any(term in lower_question for term in ["必要", "書類", "持ち物", "何が必要"]):
        section_triggers.extend(["必要なもの", "必要書類", "提出書類", "持ち物"])
    if any(term in lower_question for term in ["流れ", "方法", "出し方", "予約", "手続き"]):
        section_triggers.extend(["手続きの流れ", "利用の流れ", "流れ"])
    if any(term in lower_question for term in ["どこ", "窓口", "場所"]):
        section_triggers.extend(["受付窓口", "窓口"])
    if any(term in lower_question for term in ["注意", "できない", "対象外"]):
        section_triggers.extend(["注意"])

    if section_triggers:
        captured: list[str] = []
        capture = False
        for line in lines:
            stripped = line.strip()
            if any(trigger in stripped for trigger in section_triggers):
                capture = True
                captured.append(stripped)
                continue
            if capture:
                if not stripped:
                    if captured:
                        break
                    continue
                if ":" in stripped and not stripped.startswith("-") and not any(trigger in stripped for trigger in section_triggers):
                    break
                captured.append(stripped)
        if captured:
            return captured[:8]

    meaningful = [line.strip() for line in lines if line.strip()]
    bullets = [line for line in meaningful if line.startswith("-")]
    paragraphs = [line for line in meaningful if not line.startswith("-") and ":" not in line]
    selected = paragraphs[:2] + bullets[:4]
    return selected[:8] if selected else [excerpt(body, max_chars=240)]


def _format_answer(question: str, hits: list[SearchHit], *, style: str) -> tuple[str, list[str]]:
    if not _grounded_enough(hits):
        answer = "参照文書だけでは、この質問に十分な根拠を持って回答できません。制度名・対象者・期限・必要書類を担当課へ確認してください。"
        checks = [
            "参照文書に該当制度があるか確認してください。",
            "古いFAQや別自治体の情報を混ぜていないか確認してください。",
            "市民へ案内する前に、担当課の公式情報で確認してください。",
        ]
        return answer, checks

    top = hits[0]
    relevant_lines = _extract_relevant_lines(question, top)

    if style == "短く":
        lead = "参照文書に基づく短い回答案です。"
    elif style == "職員向け":
        lead = "以下は、参照文書に基づく職員確認用の回答素案です。"
    else:
        lead = "以下は、参照文書に基づく市民向けの回答案です。"

    answer_lines = [lead, "", f"根拠文書: {top.doc.id}「{top.doc.title}」", ""]
    answer_lines.extend(relevant_lines)

    checks = [
        "制度名、対象者、金額、期限、必要書類、受付窓口が最新か確認してください。",
        "FAQコーパスの最終確認日が古い場合は、公式ページや要綱で更新してください。",
        "この回答案は法的判断ではなく、市民案内の下書きとして扱ってください。",
    ]
    return "\n".join(answer_lines).strip(), checks


def _format_references(hits: list[SearchHit], *, grounded: bool) -> list[str]:
    if not hits:
        return ["根拠候補は見つかりませんでした。"]
    if not grounded:
        return [
            "検索候補はありましたが、質問に対する十分な根拠とは判断しませんでした。",
            *[f"候補: {hit.doc.id}「{hit.doc.title}」（score={hit.score}）" for hit in hits[:3]],
        ]
    refs: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        meta = " / ".join(f"{k}: {v}" for k, v in hit.doc.metadata.items())
        meta_suffix = f" / {meta}" if meta else ""
        refs.append("\n".join([
            f"{idx}. **{hit.doc.id}**: {hit.doc.title}（score={hit.score}, confidence={hit.confidence}{meta_suffix}）",
            f"   - source: `{hit.doc.source}`",
            f"   - matched_terms: {', '.join(hit.matched_terms) if hit.matched_terms else 'なし'}",
            f"   - excerpt: {excerpt(hit.doc.body, max_chars=260)}",
        ]))
    return refs


def _format_safety_notes(question: str, corpora: list[tuple[str, str]], pii_counts: dict[str, int]) -> list[str]:
    joined_corpus_preview = "\n".join(text[:4000] for _, text in corpora[:3])
    findings = detect_prompt_injection(question) + detect_prompt_injection(joined_corpus_preview)
    notes: list[str] = []
    if findings:
        notes.append("プロンプトインジェクションらしき文言を検出しました。入力文・参照文書の一部として扱い、アプリの挙動変更指示としては扱っていません。")
    else:
        notes.append("入力内に明確なプロンプトインジェクション文言は検出されませんでした。")
    if pii_counts:
        readable = ", ".join(f"{key}={value}" for key, value in sorted(pii_counts.items()))
        notes.append(f"個人情報らしき文字列をマスクしました: {readable}")
    else:
        notes.append("マスク対象の個人情報らしき文字列は検出されませんでした。")
    notes.append("参照文書にない情報は補完しない方針で回答しています。")
    return notes


def handle(payload: dict[str, Any]) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        question = require_text(inputs, "question", min_chars=2, max_chars=3000)
        mode = get_choice(inputs, "mode", allowed=["safe", "preserve"], default="safe")
        style = get_choice(inputs, "answer_style", allowed=["市民向け", "職員向け", "短く"], default="市民向け")
        max_results = _as_int(inputs.get("max_results"), default=3, minimum=1, maximum=6)
        retrieval_backend_name = get_choice(inputs, "retrieval_backend", allowed=["lexical", "bm25", "hybrid"], default="lexical")

        corpora = _collect_corpora(inputs)
        if not corpora:
            return error_output("参照文書がありません。`use_sample_corpus` を `yes` にするか、`documents` または `files` を入力してください。")

        pii_counts: dict[str, int] = {}
        safe_question = question
        safe_corpora = corpora
        if mode == "safe":
            redacted_question = redact_pii_with_counts(question)
            safe_question = redacted_question.text
            for key, count in redacted_question.counts.items():
                pii_counts[key] = pii_counts.get(key, 0) + count

            redacted_corpora: list[tuple[str, str]] = []
            for source, text in corpora:
                redacted = redact_pii_with_counts(text)
                redacted_corpora.append((source, redacted.text))
                for key, count in redacted.counts.items():
                    pii_counts[key] = pii_counts.get(key, 0) + count
            safe_corpora = redacted_corpora

        docs = build_documents(safe_corpora)
        backend = get_search_backend(retrieval_backend_name)
        hits = backend.search(safe_question, docs, limit=max_results)
        grounded = _grounded_enough(hits)
        answer, checks = _format_answer(safe_question, hits, style=style)

        report = markdown_report(
            "市民FAQ RAG 回答案",
            [
                ("質問", safe_question),
                ("回答案", answer),
                ("根拠", _format_references(hits, grounded=grounded)),
                ("判断", [
                    f"回答可能性: {'参照文書に基づいて回答可能' if grounded else '根拠不足のため断定不可'}",
                    f"検索ヒット数: {len(hits)}",
                    f"検索方式: {backend.name}",
                    f"回答スタイル: {style}",
                ]),
                ("担当者確認チェック", checks),
                ("安全性メモ", _format_safety_notes(safe_question, safe_corpora, pii_counts)),
                ("品質メモ", [
                    f"deterministic {backend.name} retrieverで検索しています。外部APIキーなしで再現可能です。",
                    "本番では、自治体公式FAQ・要綱・更新日付き文書に差し替えてください。",
                    "根拠なし断定を避けるため、低スコア時は担当課確認へ誘導します。",
                    f"アプリ版: {APP_VERSION}",
                ]),
            ],
        )
        return output(report)
    except (GennaiPayloadError, GennaiValidationError) as e:
        return error_output(str(e))
    except Exception as e:  # pragma: no cover
        return error_output(f"処理中に問題が発生しました: {e}")


if FastAPI:
    app = FastAPI(title="citizen-faq-rag", version=APP_VERSION)
    add_observability_routes(app, app_name="citizen_faq_rag", app_version=APP_VERSION)

    @app.post("/")
    def run(payload: dict[str, Any]) -> dict[str, str]:
        return observe_call("citizen_faq_rag", APP_VERSION, payload, lambda: handle(payload))
else:  # pragma: no cover
    app = None
