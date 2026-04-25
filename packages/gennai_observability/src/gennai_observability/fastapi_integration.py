from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .metrics import GLOBAL_REGISTRY, MetricsRegistry
from .tracing import traced_call


def observe_call(
    app_name: str,
    app_version: str,
    payload: dict[str, Any] | Any,
    handler: Callable[[], dict[str, Any]],
    *,
    registry: MetricsRegistry = GLOBAL_REGISTRY,
) -> dict[str, Any]:
    """Run a handler, record local metrics, and attach a trace id to the response."""

    request_id = None
    if isinstance(payload, dict):
        request_id = str(payload.get("request_id")) if payload.get("request_id") else None
    result, span = traced_call(handler, app_id=app_name, app_version=app_version, request_id=request_id)
    registry.record_request(app_name=app_name, status=span.status, duration_ms=span.duration_ms)
    if isinstance(result, dict):
        result.setdefault("trace_id", span.trace_id)
    return result


def add_observability_routes(
    app: Any,
    *,
    app_name: str,
    app_version: str,
    registry: MetricsRegistry = GLOBAL_REGISTRY,
) -> None:
    """Attach `/healthz`, `/metrics`, and `/observability` to a FastAPI app."""

    try:
        from fastapi.responses import PlainTextResponse
    except Exception:  # pragma: no cover
        PlainTextResponse = None

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "app": app_name, "version": app_version}

    @app.get("/metrics")
    def metrics() -> Any:
        text = registry.prometheus_text()
        if PlainTextResponse is None:  # pragma: no cover
            return text
        return PlainTextResponse(text, media_type="text/plain; version=0.0.4")

    @app.get("/observability")
    def observability() -> Any:
        text = registry.markdown_summary()
        if PlainTextResponse is None:  # pragma: no cover
            return text
        return PlainTextResponse(text, media_type="text/markdown")
