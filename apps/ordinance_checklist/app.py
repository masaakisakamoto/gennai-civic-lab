from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None


from gennai_app_kit import get_inputs, output, error_output, markdown_report, redact_pii

def handle(payload: dict) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        doc = redact_pii(str(inputs.get("document") or inputs.get("text") or "").strip())
        viewpoint = str(inputs.get("viewpoint", "条例・要綱チェック"))
        if not doc:
            return error_output("`document` または `text` を入力してください。")
        checks = [
            "目的・根拠規定が明確か",
            "対象者・対象事業が明確か",
            "申請・審査・決定・取消の手続きが明確か",
            "個人情報の扱いが明確か",
            "施行日・経過措置が必要か",
            "上位法令・既存要綱との整合性を確認したか",
        ]
        report = markdown_report(
            "条例・要綱チェックリスト",
            [
                ("観点", viewpoint),
                ("文書の抜粋", doc[:300] + ("..." if len(doc) > 300 else "")),
                ("確認項目", checks),
                ("注意", "この出力は法務確認の代替ではありません。必ず担当部門・法務担当が確認してください。"),
            ],
        )
        return output(report)
    except Exception as e:
        return error_output(f"処理中に問題が発生しました: {e}")

if FastAPI:
    app = FastAPI(title="civic-ordinance-checklist", version="0.1.0")
    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return handle(payload)
else:
    app = None
