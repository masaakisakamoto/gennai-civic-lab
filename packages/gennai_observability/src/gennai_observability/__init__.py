"""Operational observability primitives for Gennai-compatible civic AI apps."""

from .fastapi_integration import add_observability_routes, observe_call
from .metrics import GLOBAL_REGISTRY, InMemoryMetrics, MetricSample, MetricsRegistry
from .ops_report import OpsReport, build_ops_report, write_ops_reports
from .tracing import JsonlTraceExporter, TraceEvent, TraceSpan, load_trace_spans, traced_call

__all__ = [
    "GLOBAL_REGISTRY",
    "InMemoryMetrics",
    "JsonlTraceExporter",
    "MetricSample",
    "MetricsRegistry",
    "OpsReport",
    "TraceEvent",
    "TraceSpan",
    "add_observability_routes",
    "build_ops_report",
    "load_trace_spans",
    "observe_call",
    "traced_call",
    "write_ops_reports",
]
