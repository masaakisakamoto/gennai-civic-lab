from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None

from gennai_observability import add_observability_routes, observe_call

from gennai_app_kit import (
    ChatMessage,
    GennaiPayloadError,
    GennaiValidationError,
    LLMClient,
    detect_prompt_injection,
    error_output,
    get_choice,
    get_str,
    llm_from_env,
    markdown_report,
    output,
    parse_request,
    redact_pii_with_counts,
    require_text,
)

APP_VERSION = "0.7.0"
MAX_TEXT_CHARS = 12_000

REPLACEMENTS: dict[str, str] = {
    "本制度の利用に際しては": "この制度を利用するときは",
    "利用に際しては": "利用するときは",
    "本制度": "この制度",
    "利用に際して": "利用するとき",
    "所定の申請書類": "申請に必要な書類",
    "所定の": "決められた",
    "申請書類": "申請に必要な書類",
    "提出してください": "出してください",
    "該当する": "あてはまる",
    "速やかに": "できるだけ早く",
    "お問い合わせください": "聞いてください",
    "ご確認ください": "確認してください",
    "実施します": "行います",
    "対象となります": "対象です",
    "必要となります": "必要です",
    "交付します": "お渡しします",
    "納付してください": "支払ってください",
    "記載してください": "書いてください",
    "持参してください": "持ってきてください",
}

GLOSSARY: dict[str, str] = {
    "申請": "役所などにお願いを出すこと",
    "交付": "役所などが書類やお金を渡すこと",
    "納付": "お金を支払うこと",
    "減免": "支払う金額を少なくしたり、なくしたりすること",
    "対象者": "この制度を使える人",
    "要件": "必要な条件",
    "添付書類": "申請書と一緒に出す書類",
}

CHECKLIST = [
    "制度名、対象者、金額、期限、問い合わせ先が正しいか確認してください。",
    "法律・条例・要綱上の意味が変わっていないか確認してください。",
    "市民が次に何をすればよいか、1文目または最後に明確に書いてください。",
    "電話番号やメールアドレスを公開してよい文書か確認してください。",
]


def _load_prompt() -> str:
    return (Path(__file__).with_name("prompt.md")).read_text(encoding="utf-8")


@dataclass(frozen=True)
class RewriteResult:
    rewritten: str
    changed_expressions: list[str]
    glossary_notes: list[str]
    quality_notes: list[str]
    used_llm: bool = False
    llm_provider: str = "offline"
    llm_model: str = "rules"


def split_sentences(text: str) -> str:
    # Keep the algorithm intentionally conservative for legal/administrative text.
    normalized = text.replace("。", "。\n")
    lines = [line.strip() for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line)


def fallback_rewrite(text: str, *, audience: str, tone: str) -> RewriteResult:
    result = text.strip()
    changes: list[str] = []

    for hard, easy in REPLACEMENTS.items():
        if hard in result:
            result = result.replace(hard, easy)
            changes.append(f"「{hard}」→「{easy}」")

    result = split_sentences(result)

    # Add a very small amount of structure without inventing facts.
    if tone == "短く":
        result = result.replace("\n", " ")
    elif audience == "高齢者向け":
        result = "次の内容を確認してください。\n" + result
    elif audience == "子育て世帯向け":
        result = "手続きが必要な場合は、次の内容を確認してください。\n" + result

    glossary_notes = [f"{term}: {desc}" for term, desc in GLOSSARY.items() if term in text]
    quality_notes = [
        "ルールベースfallbackで書き換えました。LLMを設定すると、より自然な文章案を生成できます。",
        "元文にない制度内容は追加していません。",
    ]
    return RewriteResult(
        rewritten=result,
        changed_expressions=changes or ["大きな置換対象は見つかりませんでした。文章の区切りと確認観点を整理しました。"],
        glossary_notes=glossary_notes or ["特に補足すべき専門用語は検出されませんでした。"],
        quality_notes=quality_notes,
    )


def build_llm_messages(text: str, *, audience: str, tone: str, preserve_terms: str) -> list[ChatMessage]:
    user_prompt = f"""
対象読者: {audience}
トーン: {tone}
必ず残す語句: {preserve_terms or "なし"}

入力文:
{text}
""".strip()
    return [
        ChatMessage(role="system", content=_load_prompt()),
        ChatMessage(role="user", content=user_prompt),
    ]


def try_llm_rewrite(
    text: str,
    *,
    audience: str,
    tone: str,
    preserve_terms: str,
    client: LLMClient | None = None,
) -> RewriteResult | None:
    llm = client or llm_from_env()
    messages = build_llm_messages(text, audience=audience, tone=tone, preserve_terms=preserve_terms)
    try:
        result = llm.complete(messages, temperature=0.2)
    except Exception:
        return None

    # Offline fallback echoes prompts; don't treat it as a real rewrite.
    if result.used_fallback or result.provider == "offline":
        return None

    return RewriteResult(
        rewritten=result.text.strip(),
        changed_expressions=["LLMによる自然文の再構成を行いました。"],
        glossary_notes=["専門用語の説明はLLM出力内の『難しかった表現と説明』も確認してください。"],
        quality_notes=["LLM出力は担当者レビュー前提です。制度上の判断は人間が確認してください。"],
        used_llm=True,
        llm_provider=result.provider,
        llm_model=result.model,
    )


def render_report(
    result: RewriteResult,
    *,
    audience: str,
    tone: str,
    safety_notes: list[str],
    redaction_counts: dict[str, int],
) -> str:
    pii_note = (
        [f"{kind}: {count}件をマスクしました。" for kind, count in redaction_counts.items()]
        if redaction_counts
        else ["マスク対象の個人情報らしき文字列は検出されませんでした。"]
    )
    return markdown_report(
        "やさしい日本語への書き換え",
        [
            ("書き換え案", result.rewritten),
            ("難しかった表現と説明", result.glossary_notes),
            ("変更した主な表現", result.changed_expressions),
            ("安全性メモ", safety_notes + pii_note),
            ("担当者確認チェック", CHECKLIST),
            (
                "品質メモ",
                result.quality_notes
                + [
                    f"対象読者: {audience}",
                    f"トーン: {tone}",
                    f"生成方式: {'LLM' if result.used_llm else 'rules'} / {result.llm_provider}:{result.llm_model}",
                    f"アプリ版: {APP_VERSION}",
                ],
            ),
        ],
    )


def handle(payload: dict, *, client: LLMClient | None = None) -> dict[str, str]:
    try:
        ctx = parse_request(payload)
        text = require_text(ctx.inputs, "text", fallback_keys=("content",), max_chars=MAX_TEXT_CHARS)
        audience = get_choice(
            ctx.inputs,
            "audience",
            allowed=["市民向け", "高齢者向け", "子育て世帯向け", "職員向け"],
            default="市民向け",
        )
        tone = get_choice(
            ctx.inputs,
            "tone",
            allowed=["やさしい", "丁寧", "短く"],
            default="やさしい",
        )
        mode = get_choice(
            ctx.inputs,
            "mode",
            allowed=["safe", "preserve"],
            default="safe",
        )
        preserve_terms = get_str(ctx.inputs, "preserve_terms", default="", max_chars=1000)

        safety_findings = detect_prompt_injection(text)
        safety_notes = [finding.message for finding in safety_findings]
        if not safety_notes:
            safety_notes = ["入力内に明確なプロンプトインジェクション文言は検出されませんでした。"]

        redaction_counts: dict[str, int] = {}
        source_text = text
        if mode == "safe":
            redacted = redact_pii_with_counts(text)
            source_text = redacted.text
            redaction_counts = redacted.counts

        result = try_llm_rewrite(
            source_text,
            audience=audience,
            tone=tone,
            preserve_terms=preserve_terms,
            client=client,
        ) or fallback_rewrite(source_text, audience=audience, tone=tone)

        report = render_report(
            result,
            audience=audience,
            tone=tone,
            safety_notes=safety_notes,
            redaction_counts=redaction_counts,
        )
        return output(report)
    except (GennaiPayloadError, GennaiValidationError) as exc:
        return error_output(str(exc), title="入力エラー")
    except Exception as exc:  # pragma: no cover - last-resort safety net
        return error_output(f"処理中に問題が発生しました: {exc}")


if FastAPI:
    app = FastAPI(title="gennai-civic-easy-japanese", version=APP_VERSION)
    add_observability_routes(app, app_name="easy_japanese_rewriter", app_version=APP_VERSION)

    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return observe_call("easy_japanese_rewriter", APP_VERSION, payload, lambda: handle(payload))
else:  # pragma: no cover
    app = None


if __name__ == "__main__":
    demo = {
        "inputs": {
            "text": "本制度の利用に際しては、所定の申請書類を提出してください。詳細は担当課へお問い合わせください。",
            "audience": "市民向け",
            "tone": "やさしい",
            "mode": "safe",
        }
    }
    print(handle(demo)["outputs"])
