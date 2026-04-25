from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from .core import SafetyFinding, new_request_id, redact_pii_with_counts


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any, *, length: int = 16) -> str:
    """Return a stable, non-reversible short fingerprint for audit correlation.

    The goal is traceability without storing raw user text. This is not a security
    boundary; use it as lightweight operational metadata for local demos and OSS
    examples.
    """

    data = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:length]


def summarize_inputs(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Create a PII-conscious summary of a Gennai ``inputs`` object.

    Values are not stored verbatim. Text-like values are redacted and then summarized by
    character length and fingerprint. This lets developers inspect request flow without
    accidentally committing personal data to logs.
    """

    summary: dict[str, Any] = {}
    for key, value in sorted(inputs.items()):
        if key == "files" and isinstance(value, list):
            summary[key] = {"kind": "files", "count": len(value)}
            continue
        if isinstance(value, str):
            redacted = redact_pii_with_counts(value)
            summary[key] = {
                "kind": "text",
                "chars": len(value),
                "fingerprint": stable_hash(redacted.text),
                "redactions": redacted.counts,
            }
            continue
        if isinstance(value, (int, float, bool)) or value is None:
            summary[key] = {"kind": type(value).__name__, "value": value}
            continue
        summary[key] = {
            "kind": type(value).__name__,
            "fingerprint": stable_hash(value),
        }
    return summary


@dataclass(frozen=True)
class AuditEvent:
    schema_version: str
    app_id: str
    app_version: str
    request_id: str
    started_at: str
    completed_at: str
    duration_ms: float
    input_summary: dict[str, Any]
    output_chars: int
    safety_findings: list[dict[str, Any]] = field(default_factory=list)
    eval_case: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


class AuditTimer:
    """Small helper for measuring an app call and creating a structured audit event."""

    def __init__(self) -> None:
        self.started_at = utc_now()
        self._started = perf_counter()

    def finish(
        self,
        *,
        app_id: str,
        app_version: str,
        payload: Mapping[str, Any],
        outputs: str,
        safety_findings: Sequence[SafetyFinding] | None = None,
        eval_case: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AuditEvent:
        completed_at = utc_now()
        duration_ms = round((perf_counter() - self._started) * 1000, 3)
        inputs = payload.get("inputs", {}) if isinstance(payload, Mapping) else {}
        if not isinstance(inputs, Mapping):
            inputs = {}
        findings = [
            {
                "kind": finding.kind,
                "severity": finding.severity,
                "message": finding.message,
            }
            for finding in (safety_findings or [])
        ]
        return AuditEvent(
            schema_version="gennai.audit.v1",
            app_id=app_id,
            app_version=app_version,
            request_id=str(payload.get("request_id") or new_request_id(payload)),
            started_at=self.started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            input_summary=summarize_inputs(inputs),
            output_chars=len(outputs),
            safety_findings=findings,
            eval_case=eval_case,
            metadata=dict(metadata or {}),
        )


def append_audit_event(path: str | Path, event: AuditEvent) -> None:
    """Append an audit event as JSONL, creating parent directories when needed."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(event.to_json() + "\n")


def create_audit_event(
    *,
    app_id: str,
    app_version: str,
    payload: Mapping[str, Any],
    outputs: str,
    duration_ms: float = 0.0,
    safety_findings: Sequence[SafetyFinding] | None = None,
    eval_case: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AuditEvent:
    """Create an audit event when a caller already measured duration externally."""

    inputs = payload.get("inputs", {}) if isinstance(payload, Mapping) else {}
    if not isinstance(inputs, Mapping):
        inputs = {}
    findings = [
        {
            "kind": finding.kind,
            "severity": finding.severity,
            "message": finding.message,
        }
        for finding in (safety_findings or [])
    ]
    now = utc_now()
    return AuditEvent(
        schema_version="gennai.audit.v1",
        app_id=app_id,
        app_version=app_version,
        request_id=str(payload.get("request_id") or new_request_id(payload)),
        started_at=now,
        completed_at=now,
        duration_ms=round(float(duration_ms), 3),
        input_summary=summarize_inputs(inputs),
        output_chars=len(outputs),
        safety_findings=findings,
        eval_case=eval_case,
        metadata=dict(metadata or {}),
    )
