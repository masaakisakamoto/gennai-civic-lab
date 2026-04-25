from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "gennai_observability" / "src"))

from gennai_observability import JsonlTraceExporter, TraceEvent, traced_call


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate safe demo traces for the operational report")
    parser.add_argument("--output", default="reports/traces.jsonl")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.output)
    if path.exists():
        path.unlink()
    exporter = JsonlTraceExporter(path)

    traced_call(
        lambda: {"outputs": "ok"},
        app_id="easy_japanese_rewriter",
        app_version="0.7.0",
        exporter=exporter,
        metadata={"mode": "safe"},
        events=[TraceEvent("rewrite.completed", metadata={"redactions": 0})],
    )
    traced_call(
        lambda: {"outputs": "ok"},
        app_id="citizen_faq_rag",
        app_version="0.7.0",
        exporter=exporter,
        metadata={"retrieval_backend": "hybrid"},
        events=[
            TraceEvent("retrieval.completed", metadata={"backend": "hybrid", "hits": 3}),
            TraceEvent("grounding.checked", metadata={"answerable": True}),
        ],
    )
    traced_call(
        lambda: {"outputs": "abstained"},
        app_id="citizen_faq_rag",
        app_version="0.7.0",
        exporter=exporter,
        metadata={"retrieval_backend": "hybrid"},
        events=[
            TraceEvent("retrieval.completed", metadata={"backend": "hybrid", "hits": 1}),
            TraceEvent("grounding.checked", metadata={"answerable": False}),
        ],
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
