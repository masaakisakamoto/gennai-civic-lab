from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .metrics import InMemoryMetrics
from .tracing import TraceSpan, load_trace_spans


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OpsReport:
    schema_version: str
    generated_at: str
    eval_total: int
    eval_passed: int
    eval_failed: int
    trace_total: int
    trace_ok: int
    trace_error: int
    apps_seen: dict[str, int]
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_eval_report(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"total": 0, "passed": 0, "failed": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def build_ops_report(*, eval_json: str | Path | None = None, traces_jsonl: str | Path | None = None) -> OpsReport:
    eval_data = _load_eval_report(Path(eval_json) if eval_json else None)
    spans: list[TraceSpan] = load_trace_spans(traces_jsonl) if traces_jsonl else []

    metrics = InMemoryMetrics()
    for span in spans:
        metrics.observe_span(span)

    statuses = Counter(span.status for span in spans)
    apps = Counter(span.app_id for span in spans)

    notes: list[str] = []
    if eval_data.get("failed", 0):
        notes.append("Some eval cases failed. Do not promote this build without investigation.")
    else:
        notes.append("No failed eval cases were reported.")
    if statuses.get("error", 0):
        notes.append("Some traced requests ended with errors. Inspect trace JSONL before deployment.")
    else:
        notes.append("No traced request errors were reported.")
    notes.append("This report stores operational metadata only. Avoid logging raw citizen text or documents.")

    return OpsReport(
        schema_version="gennai.ops_report.v1",
        generated_at=utc_now(),
        eval_total=int(eval_data.get("total", 0)),
        eval_passed=int(eval_data.get("passed", 0)),
        eval_failed=int(eval_data.get("failed", 0)),
        trace_total=len(spans),
        trace_ok=statuses.get("ok", 0),
        trace_error=statuses.get("error", 0),
        apps_seen=dict(sorted(apps.items())),
        metrics=metrics.summary(),
        notes=notes,
    )


def write_json(path: Path, report: OpsReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, report: OpsReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gennai Operational Report",
        "",
        f"- generated_at: `{report.generated_at}`",
        f"- eval: **{report.eval_passed}/{report.eval_total} passed**",
        f"- traces: **{report.trace_total} total**, **{report.trace_ok} ok**, **{report.trace_error} error**",
        "",
        "## Apps Seen",
        "",
    ]
    if report.apps_seen:
        for app_id, count in sorted(report.apps_seen.items()):
            lines.append(f"- `{app_id}`: {count} traced request(s)")
    else:
        lines.append("- No trace spans were provided.")
    lines.extend(["", "## Metrics", "", "| metric | labels | count | avg | p95 | max |", "|---|---|---:|---:|---:|---:|"])
    for metric in report.metrics.get("metrics", []):
        labels = ", ".join(f"{k}={v}" for k, v in metric.get("labels", {}).items()) or "-"
        lines.append(
            f"| `{metric['name']}` | {labels} | {metric['count']} | {metric['avg']} | {metric['p95']} | {metric['max']} |"
        )
    lines.extend(["", "## Notes", ""])
    for note in report.notes:
        lines.append(f"- {note}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ops_reports(*, report: OpsReport, markdown_path: str | Path, json_path: str | Path) -> None:
    write_markdown(Path(markdown_path), report)
    write_json(Path(json_path), report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an operational report for Gennai-compatible apps")
    parser.add_argument("--eval-json", default="reports/eval-report.json")
    parser.add_argument("--traces-jsonl", default="reports/traces.jsonl")
    parser.add_argument("--markdown-report", default="reports/ops-report.md")
    parser.add_argument("--json-report", default="reports/ops-report.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_ops_report(eval_json=args.eval_json, traces_jsonl=args.traces_jsonl)
    write_ops_reports(report=report, markdown_path=args.markdown_report, json_path=args.json_report)
    print(f"wrote {args.markdown_report} and {args.json_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
