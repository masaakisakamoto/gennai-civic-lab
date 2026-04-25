from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any

from .tracing import TraceSpan


@dataclass(frozen=True)
class MetricSample:
    name: str
    value: float
    labels: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InMemoryMetrics:
    """Tiny metrics collector for demos and tests.

    It is deliberately dependency-free. Production deployments can replace it with
    Prometheus, CloudWatch, Azure Monitor, or OpenTelemetry exporters.
    """

    def __init__(self) -> None:
        self.samples: list[MetricSample] = []

    def observe(self, name: str, value: float, **labels: str) -> None:
        self.samples.append(MetricSample(name=name, value=float(value), labels=dict(labels)))

    def observe_span(self, span: TraceSpan) -> None:
        self.observe("request_duration_ms", span.duration_ms, app_id=span.app_id, status=span.status)
        self.observe("request_total", 1, app_id=span.app_id, status=span.status)

    def summary(self) -> dict[str, Any]:
        grouped: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(list)
        for sample in self.samples:
            key = (sample.name, tuple(sorted(sample.labels.items())))
            grouped[key].append(sample.value)

        rows: list[dict[str, Any]] = []
        for (name, labels), values in sorted(grouped.items()):
            ordered = sorted(values)
            p95_index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
            rows.append(
                {
                    "name": name,
                    "labels": dict(labels),
                    "count": len(values),
                    "sum": round(sum(values), 3),
                    "avg": round(mean(values), 3),
                    "min": round(min(values), 3),
                    "max": round(max(values), 3),
                    "p95": round(ordered[p95_index], 3),
                }
            )
        return {"schema_version": "gennai.metrics.v1", "metrics": rows}


class MetricsRegistry(InMemoryMetrics):
    """Small compatibility wrapper used by the FastAPI integration."""

    def record_request(self, *, app_name: str, status: str, duration_ms: float) -> None:
        self.observe("gennai_request_total", 1, app=app_name, status=status)
        self.observe("gennai_request_duration_ms", duration_ms, app=app_name, status=status)

    def prometheus_text(self) -> str:
        lines = [
            "# HELP gennai_request_total Total Gennai-compatible app requests recorded locally.",
            "# TYPE gennai_request_total counter",
        ]
        summary = self.summary()["metrics"]
        for row in summary:
            name = row["name"]
            labels = row["labels"]
            if name == "gennai_request_total":
                label_text = ",".join(f'{k}="{v}"' for k, v in labels.items())
                lines.append(f"{name}{{{label_text}}} {int(row['sum'])}")
        lines.extend([
            "# HELP gennai_request_duration_ms Gennai-compatible app request duration in milliseconds.",
            "# TYPE gennai_request_duration_ms summary",
        ])
        for row in summary:
            name = row["name"]
            labels = row["labels"]
            if name == "gennai_request_duration_ms":
                label_text = ",".join(f'{k}="{v}"' for k, v in labels.items())
                lines.append(f"{name}_count{{{label_text}}} {row['count']}")
                lines.append(f"{name}_sum{{{label_text}}} {row['sum']}")
                lines.append(f"{name}_p95{{{label_text}}} {row['p95']}")
        return "\n".join(lines) + "\n"

    def markdown_summary(self) -> str:
        rows = self.summary()["metrics"]
        lines = [
            "# Gennai Observability",
            "",
            "| metric | labels | count | avg | p95 | max |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for row in rows:
            labels = ", ".join(f"{k}={v}" for k, v in row["labels"].items()) or "-"
            lines.append(f"| `{row['name']}` | {labels} | {row['count']} | {row['avg']} | {row['p95']} | {row['max']} |")
        return "\n".join(lines) + "\n"


GLOBAL_REGISTRY = MetricsRegistry()
