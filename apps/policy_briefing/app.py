from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None


from gennai_app_kit import get_inputs, output, error_output, markdown_report, redact_pii

def handle(payload: dict) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        text = redact_pii(str(inputs.get("text") or inputs.get("document") or "").strip())
        if not text:
            return error_output("`text` または `document` を入力してください。")
        report = markdown_report(
            "政策ブリーフィング",
            [
                ("要旨", text[:300] + ("..." if len(text) > 300 else "")),
                ("論点", ["目的は明確か", "対象者は明確か", "費用対効果を説明できるか", "関係者調整が必要か"]),
                ("リスク", ["予算不足", "スケジュール遅延", "市民説明不足", "制度変更の可能性"]),
                ("意思決定者への確認事項", ["実施可否", "予算枠", "優先順位", "説明責任の観点"]),
            ],
        )
        return output(report)
    except Exception as e:
        return error_output(f"処理中に問題が発生しました: {e}")

if FastAPI:
    app = FastAPI(title="civic-policy-briefing", version="0.1.0")
    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return handle(payload)
else:
    app = None
