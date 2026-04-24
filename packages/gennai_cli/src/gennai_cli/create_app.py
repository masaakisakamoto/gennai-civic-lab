from __future__ import annotations
import sys
from pathlib import Path

TEMPLATE = """from __future__ import annotations

try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None

from gennai_app_kit import get_inputs, output, error_output, markdown_report

def handle(payload: dict) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        text = str(inputs.get("text", ""))
        report = markdown_report("{title}", [("入力", text), ("結果", "ここに処理結果を実装します")])
        return output(report)
    except Exception as e:
        return error_output(f"処理中に問題が発生しました: {e}")

if FastAPI:
    app = FastAPI(title="{name}", version="0.1.0")
    @app.post("/")
    def run(payload: dict) -> dict[str, str]:
        return handle(payload)
else:
    app = None
"""

def main(argv: list[str]) -> int:
    if not argv:
        print("usage: create_app.py app_name")
        return 2
    name = argv[0].replace("-", "_")
    target = Path("apps") / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "__init__.py").write_text("", encoding="utf-8")
    (target / "app.py").write_text(TEMPLATE.format(name=name, title=name.replace("_", " ").title()), encoding="utf-8")
    (target / "README.md").write_text(f"# {name}\n\n源内互換AIアプリの雛形です。\n", encoding="utf-8")
    print(f"created {target}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
