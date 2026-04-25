from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[str(key)] = value
        else:
            safe[str(key)] = str(value)
    return safe


@dataclass(frozen=True)
class TraceEvent:
    """A small event inside a request trace.

    Events intentionally store operational facts, not raw user prompts. For example,
    use ``{"documents": 4}`` or ``{"retrieval_backend": "hybrid"}``, not the full
    citizen question or document body.
    """

    name: str
    at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraceSpan:
    schema_version: str
    trace_id: str
    request_id: str
    app_id: str
    app_version: str
    started_at: str
    completed_at: str
    duration_ms: float
    status: str
    events: list[TraceEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [event.to_dict() for event in self.events]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


class JsonlTraceExporter:
    """Append trace spans to a JSONL file.

    This is intentionally boring infrastructure: easy to inspect, easy to commit to
    demo reports, and easy to replace with OpenTelemetry or cloud logging later.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def export(self, span: TraceSpan) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(span.to_json() + "\n")


def traced_call(
    func: Callable[[], T],
    *,
    app_id: str,
    app_version: str,
    request_id: str | None = None,
    exporter: JsonlTraceExporter | None = None,
    metadata: Mapping[str, Any] | None = None,
    events: list[TraceEvent] | None = None,
) -> tuple[T, TraceSpan]:
    """Run ``func`` and return both its result and a PII-conscious trace span."""

    trace_id = uuid.uuid4().hex[:16]
    req_id = request_id or uuid.uuid4().hex[:16]
    started = utc_now()
    start = time.perf_counter()
    status = "ok"
    result: T
    try:
        result = func()
    except Exception:
        status = "error"
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        span = TraceSpan(
            schema_version="gennai.trace.v1",
            trace_id=trace_id,
            request_id=req_id,
            app_id=app_id,
            app_version=app_version,
            started_at=started,
            completed_at=utc_now(),
            duration_ms=duration_ms,
            status=status,
            events=events or [],
            metadata=_safe_metadata(metadata),
        )
        if exporter:
            exporter.export(span)
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    span = TraceSpan(
        schema_version="gennai.trace.v1",
        trace_id=trace_id,
        request_id=req_id,
        app_id=app_id,
        app_version=app_version,
        started_at=started,
        completed_at=utc_now(),
        duration_ms=duration_ms,
        status=status,
        events=events or [],
        metadata=_safe_metadata(metadata),
    )
    if exporter:
        exporter.export(span)
    return result, span


def load_trace_spans(path: str | Path) -> list[TraceSpan]:
    target = Path(path)
    if not target.exists():
        return []
    spans: list[TraceSpan] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        events = [TraceEvent(**event) for event in raw.get("events", [])]
        spans.append(
            TraceSpan(
                schema_version=raw["schema_version"],
                trace_id=raw["trace_id"],
                request_id=raw["request_id"],
                app_id=raw["app_id"],
                app_version=raw["app_version"],
                started_at=raw["started_at"],
                completed_at=raw["completed_at"],
                duration_ms=float(raw["duration_ms"]),
                status=raw["status"],
                events=events,
                metadata=dict(raw.get("metadata", {})),
            )
        )
    return spans
