from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

APP_TEMPLATE = """from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None

from gennai_app_kit import GennaiValidationError, error_output, get_inputs, markdown_report, output, require_text

APP_VERSION = "0.1.0"


def handle(payload: dict[str, Any]) -> dict[str, str]:
    try:
        inputs = get_inputs(payload)
        text = require_text(inputs, "text", min_chars=1, max_chars=20000)
        report = markdown_report(
            "{title}",
            [
                ("入力", text),
                ("結果", "ここに処理結果を実装します。"),
                ("品質メモ", ["源内互換の `outputs` 形式で返しています。", f"アプリ版: {{APP_VERSION}}"]),
            ],
        )
        return output(report)
    except GennaiValidationError as e:
        return error_output(str(e))
    except Exception as e:  # pragma: no cover
        return error_output(f"処理中に問題が発生しました: {{e}}")


if FastAPI:
    app = FastAPI(title="{app_name}", version=APP_VERSION)

    @app.post("/")
    def run(payload: dict[str, Any]) -> dict[str, str]:
        return handle(payload)
else:  # pragma: no cover
    app = None
"""

README_TEMPLATE = """# {app_name}

源内互換AIアプリの雛形です。

## Run

```bash
uvicorn apps.{app_name}.app:app --reload --port 8999
```

## Request

```json
{{
  "inputs": {{
    "text": "入力テキスト"
  }}
}}
```

## Response

```json
{{
  "outputs": "# Markdown ..."
}}
```
"""

TEST_TEMPLATE = """from apps.{app_name}.app import handle


def test_{app_name}_handle() -> None:
    result = handle({{"inputs": {{"text": "テスト入力"}}}})
    assert "outputs" in result
    assert "{title}" in result["outputs"]
"""

EVAL_TEMPLATE = """app: {app_name}
cases:
  - name: basic
    input:
      inputs:
        text: テスト入力
    expect_contains:
      - {title}
      - 結果
"""

MANIFEST_TEMPLATE = {
    "text": {
        "type": "textarea",
        "title": "入力テキスト",
        "desc": "処理したいテキストを入力してください。",
        "required": True,
        "min_length": 1,
        "max_length": 20000,
    }
}


@dataclass(frozen=True)
class ScaffoldResult:
    app_name: str
    created: list[Path]


def sanitize_app_name(name: str) -> str:
    normalized = name.strip().replace("-", "_").casefold()
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError("app name is empty after normalization")
    if normalized[0].isdigit():
        normalized = f"app_{normalized}"
    return normalized


def scaffold_app(name: str, *, root: Path = Path("."), force: bool = False) -> ScaffoldResult:
    app_name = sanitize_app_name(name)
    title = app_name.replace("_", " ").title()
    targets = {
        root / "apps" / app_name / "__init__.py": "",
        root / "apps" / app_name / "app.py": APP_TEMPLATE.format(app_name=app_name, title=title),
        root / "apps" / app_name / "README.md": README_TEMPLATE.format(app_name=app_name),
        root / "manifests" / f"{app_name}.gennai.json": json.dumps(MANIFEST_TEMPLATE, ensure_ascii=False, indent=2) + "\\n",
        root / "evals" / f"{app_name}.yaml": EVAL_TEMPLATE.format(app_name=app_name, title=title),
        root / "tests" / f"test_{app_name}.py": TEST_TEMPLATE.format(app_name=app_name, title=title),
    }

    collisions = [path for path in targets if path.exists() and not force]
    if collisions:
        joined = ", ".join(str(path) for path in collisions)
        raise FileExistsError(f"refusing to overwrite existing files: {joined}")

    created: list[Path] = []
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path)
    return ScaffoldResult(app_name=app_name, created=created)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Gennai-compatible AI app scaffold")
    parser.add_argument("name", help="app name, e.g. document-risk-checker")
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--force", action="store_true", help="overwrite generated files")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = scaffold_app(args.name, root=Path(args.root), force=args.force)
    except Exception as e:
        print(f"error: {e}")
        return 1

    print(f"created app: {result.app_name}")
    for path in result.created:
        print(f"- {path}")
    print("\\nNext:")
    print(f"  uvicorn apps.{result.app_name}.app:app --reload --port 8999")
    print(f"  python packages/gennai_evals/src/gennai_evals/runner.py evals/{result.app_name}.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
