from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _split_items(value: str) -> list[str]:
    if not value:
        return []
    # Support semicolon, Japanese comma, and newline-delimited cells.
    raw = value.replace("、", ";").replace("\n", ";").split(";")
    return [item.strip() for item in raw if item.strip()]


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return _read_jsonl(path)
    raise ValueError("supported input formats: .csv, .jsonl, .ndjson")


def render_markdown(rows: list[dict[str, Any]], *, title: str = "Imported FAQ Corpus") -> str:
    lines = [
        f"# {title}",
        "",
        "このファイルは `scripts/import_faq_corpus.py` により生成されました。",
        "実運用では、各項目の更新日・担当課・公式URLを必ず確認してください。",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        faq_id = str(row.get("id") or row.get("faq_id") or f"FAQ-{index:03d}").strip()
        faq_title = str(row.get("title") or row.get("question") or "Untitled FAQ").strip()
        lines.extend([f"## {faq_id} {faq_title}"])
        meta_map = {
            "カテゴリ": row.get("category"),
            "対象": row.get("target"),
            "担当課": row.get("department"),
            "最終確認日": row.get("last_reviewed") or row.get("reviewed_at"),
            "公式URL": row.get("source_url") or row.get("url"),
        }
        for key, value in meta_map.items():
            if value:
                lines.append(f"{key}: {str(value).strip()}")
        lines.append("")

        body = str(row.get("body") or row.get("answer") or "").strip()
        if body:
            lines.extend([body, ""])

        required = _split_items(str(row.get("required_items") or row.get("documents") or ""))
        if required:
            lines.append("必要なもの:")
            lines.extend(f"- {item}" for item in required)
            lines.append("")

        flow = _split_items(str(row.get("flow") or row.get("steps") or ""))
        if flow:
            lines.append("手続きの流れ:")
            lines.extend(f"- {item}" for item in flow)
            lines.append("")

        notes = str(row.get("notes") or row.get("caution") or "").strip()
        if notes:
            lines.extend([f"注意: {notes}", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert FAQ CSV/JSONL into citizen_faq_rag Markdown corpus")
    parser.add_argument("--input", required=True, help="input .csv, .jsonl, or .ndjson file")
    parser.add_argument("--output", required=True, help="output Markdown corpus path")
    parser.add_argument("--title", default="Imported FAQ Corpus", help="top-level corpus title")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = load_rows(input_path)
    if not rows:
        print("error: input has no rows")
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(rows, title=args.title), encoding="utf-8")
    print(f"wrote {len(rows)} FAQ items to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
