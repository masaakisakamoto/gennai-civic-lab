from __future__ import annotations

import json

from gennai_observability import JsonlTraceExporter, traced_call
from gennai_observability.ops_report import build_ops_report, write_ops_reports


def test_ops_report_combines_eval_and_trace_data(tmp_path):
    eval_json = tmp_path / "eval-report.json"
    eval_json.write_text(
        json.dumps({"total": 2, "passed": 2, "failed": 0}, ensure_ascii=False),
        encoding="utf-8",
    )
    traces = tmp_path / "traces.jsonl"
    exporter = JsonlTraceExporter(traces)
    traced_call(lambda: {"outputs": "ok"}, app_id="citizen_faq_rag", app_version="0.6.0", exporter=exporter)

    report = build_ops_report(eval_json=eval_json, traces_jsonl=traces)

    assert report.eval_passed == 2
    assert report.trace_total == 1
    assert report.apps_seen["citizen_faq_rag"] == 1


def test_ops_report_writes_markdown_and_json(tmp_path):
    report = build_ops_report(eval_json=None, traces_jsonl=None)
    md = tmp_path / "ops.md"
    js = tmp_path / "ops.json"

    write_ops_reports(report=report, markdown_path=md, json_path=js)

    assert "Gennai Operational Report" in md.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["schema_version"] == "gennai.ops_report.v1"
