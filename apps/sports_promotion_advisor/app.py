from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None


from gennai_app_kit import get_inputs, output, error_output, markdown_report

def handle(payload: dict) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        audience = str(inputs.get("audience", "市民全体"))
        goal = str(inputs.get("goal", "運動習慣の定着"))
        budget = str(inputs.get("budget", "小規模"))
        constraints = str(inputs.get("constraints", "公共施設・学校・地域団体と連携"))
        initiatives = [
            f"{audience}向けの週1回参加型プログラムを設計する",
            "既存施設を活用し、初期費用を抑える",
            "地域スポーツ団体・学校・企業を巻き込む",
            "参加後アンケートと継続率で効果測定する",
        ]
        kpis = ["参加者数", "継続参加率", "初参加者比率", "満足度", "健康・交流に関する自己評価"]
        report = markdown_report(
            "スポーツ振興施策アドバイザー",
            [
                ("前提", f"対象: {audience}\n目的: {goal}\n予算感: {budget}\n制約: {constraints}"),
                ("施策案", initiatives),
                ("KPI", kpis),
                ("リスク", ["参加者の固定化", "安全管理・熱中症対策", "広報不足", "指導者不足"]),
                ("次にやること", ["対象者インタビュー", "既存事業の棚卸し", "小規模PoCの設計", "予算・協力団体の確認"]),
            ],
        )
        return output(report)
    except Exception as e:
        return error_output(f"処理中に問題が発生しました: {e}")

if FastAPI:
    app = FastAPI(title="civic-sports-promotion-advisor", version="0.1.0")
    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return handle(payload)
else:
    app = None
