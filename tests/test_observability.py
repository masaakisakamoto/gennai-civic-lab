from __future__ import annotations

import json

from gennai_observability import InMemoryMetrics, JsonlTraceExporter, TraceEvent, traced_call
from gennai_observability.tracing import load_trace_spans


def test_traced_call_exports_jsonl_without_raw_payload(tmp_path):
    path = tmp_path / "traces.jsonl"
    exporter = JsonlTraceExporter(path)

    result, span = traced_call(
        lambda: {"outputs": "ok"},
        app_id="citizen_faq_rag",
        app_version="0.6.0",
        request_id="req-1",
        exporter=exporter,
        metadata={"retrieval_backend": "hybrid"},
        events=[TraceEvent("retrieval.completed", metadata={"hits": 3})],
    )

    assert result["outputs"] == "ok"
    assert span.status == "ok"
    assert span.duration_ms >= 0
    raw = path.read_text(encoding="utf-8")
    assert "citizen_faq_rag" in raw
    assert "retrieval.completed" in raw
    assert "子ども医療費" not in raw
    loaded = load_trace_spans(path)
    assert loaded[0].request_id == "req-1"


def test_metrics_summary_from_spans(tmp_path):
    path = tmp_path / "traces.jsonl"
    exporter = JsonlTraceExporter(path)
    _, span = traced_call(lambda: 1, app_id="easy_japanese_rewriter", app_version="0.6.0", exporter=exporter)

    metrics = InMemoryMetrics()
    metrics.observe_span(span)
    summary = metrics.summary()

    assert summary["schema_version"] == "gennai.metrics.v1"
    names = {row["name"] for row in summary["metrics"]}
    assert {"request_duration_ms", "request_total"}.issubset(names)


def test_trace_json_is_machine_readable(tmp_path):
    path = tmp_path / "traces.jsonl"
    exporter = JsonlTraceExporter(path)
    traced_call(lambda: "ok", app_id="a", app_version="1", exporter=exporter)
    line = path.read_text(encoding="utf-8").splitlines()[0]
    parsed = json.loads(line)
    assert parsed["schema_version"] == "gennai.trace.v1"
    assert parsed["status"] == "ok"



def test_observe_call_adds_trace_id_and_records_metrics():
    from gennai_observability import MetricsRegistry, observe_call

    registry = MetricsRegistry()
    result = observe_call(
        "easy_japanese_rewriter",
        "0.6.0",
        {"request_id": "req-x", "inputs": {}},
        lambda: {"outputs": "ok"},
        registry=registry,
    )

    assert result["outputs"] == "ok"
    assert result["trace_id"]
    prometheus = registry.prometheus_text()
    assert "gennai_request_total" in prometheus
    assert "easy_japanese_rewriter" in prometheus
