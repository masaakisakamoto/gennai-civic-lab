from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None


from gennai_app_kit import get_inputs, output, error_output, markdown_report, redact_pii

DECISION_HINTS = ["決定", "承認", "合意", "採択", "実施する", "行う"]
TODO_HINTS = ["宿題", "対応", "確認", "担当", "次回", "期限"]
RISK_HINTS = ["懸念", "リスク", "課題", "不足", "遅延", "反対"]

def pick_sentences(text: str, hints: list[str], limit: int = 5) -> list[str]:
    sentences = [s.strip() for s in text.replace("\n", "。").split("。") if s.strip()]
    hits = [s for s in sentences if any(h in s for h in hints)]
    return hits[:limit]

def handle(payload: dict) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        body = redact_pii(str(inputs.get("transcript") or inputs.get("text") or ""))
        if not body.strip():
            return error_output("`transcript` または `text` を入力してください。")
        summary = body[:240] + ("..." if len(body) > 240 else "")
        report = markdown_report(
            "会議録サマリー",
            [
                ("概要", summary),
                ("決定事項候補", pick_sentences(body, DECISION_HINTS)),
                ("ToDo候補", pick_sentences(body, TODO_HINTS)),
                ("リスク・論点候補", pick_sentences(body, RISK_HINTS)),
                ("注意", "これは抽出補助です。正式な議事録化前に参加者確認を行ってください。"),
            ],
        )
        return output(report)
    except Exception as e:
        return error_output(f"処理中に問題が発生しました: {e}")

if FastAPI:
    app = FastAPI(title="civic-meeting-summarizer", version="0.1.0")
    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return handle(payload)
else:
    app = None
