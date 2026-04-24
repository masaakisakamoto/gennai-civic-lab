from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, TypeAlias

Markdown: TypeAlias = str


class GennaiPayloadError(ValueError):
    """Raised when an incoming Gennai-compatible request is malformed."""


class GennaiValidationError(ValueError):
    """Raised when an app-level input validation fails."""


@dataclass(frozen=True)
class RequestContext:
    """Normalized request wrapper for Gennai-compatible AI apps.

    The public contract remains simple: apps receive a JSON object with an ``inputs`` object.
    This wrapper centralizes metadata handling so each app does not reimplement it.
    """

    inputs: dict[str, Any]
    request_id: str
    received_at: str
    conversation_history: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


def new_request_id(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def get_inputs(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise GennaiPayloadError("payload must be a JSON object")
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        raise GennaiPayloadError("payload must contain an object field named 'inputs'")
    return inputs


def parse_request(payload: Mapping[str, Any]) -> RequestContext:
    inputs = get_inputs(payload)
    history = inputs.get("conversation_history")
    return RequestContext(
        inputs=inputs,
        request_id=str(payload.get("request_id") or new_request_id(payload)),
        received_at=datetime.now(timezone.utc).isoformat(),
        conversation_history=str(history) if history not in (None, "") else None,
        raw=payload,
    )


def output(markdown: Markdown) -> dict[str, str]:
    """Return the synchronous Gennai-compatible response object."""

    return {"outputs": str(markdown)}


def error_output(message: str, *, title: str = "エラー") -> dict[str, str]:
    return output(f"## {title}\n\n{message}")


def get_str(
    inputs: Mapping[str, Any],
    key: str,
    *,
    default: str = "",
    max_chars: int | None = None,
    strip: bool = True,
) -> str:
    value = inputs.get(key, default)
    if value is None:
        value = default
    text = str(value)
    if strip:
        text = text.strip()
    if max_chars is not None and len(text) > max_chars:
        raise GennaiValidationError(f"`{key}` must be at most {max_chars} characters")
    return text


def require_text(
    inputs: Mapping[str, Any],
    key: str,
    *,
    fallback_keys: Iterable[str] = (),
    min_chars: int = 1,
    max_chars: int = 20_000,
) -> str:
    keys = [key, *fallback_keys]
    for candidate in keys:
        text = get_str(inputs, candidate, max_chars=max_chars)
        if len(text) >= min_chars:
            return text
    raise GennaiValidationError(
        f"`{key}` is required" if not fallback_keys else f"one of {keys!r} is required"
    )


def get_choice(
    inputs: Mapping[str, Any],
    key: str,
    *,
    allowed: Iterable[str],
    default: str,
) -> str:
    allowed_set = set(allowed)
    value = get_str(inputs, key, default=default)
    if value not in allowed_set:
        return default
    return value


def parse_checkbox(value: Any) -> list[str]:
    """Normalize Gennai checkbox values.

    Gennai Web currently sends multiple checkbox selections as a comma-separated string.
    """

    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


@dataclass(frozen=True)
class NormalizedFile:
    key: str
    filename: str
    content_base64: str

    def bytes(self) -> bytes:
        return base64.b64decode(self.content_base64)

    def text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
        return self.bytes().decode(encoding, errors=errors)


def normalize_files(inputs: Mapping[str, Any]) -> list[NormalizedFile]:
    raw_files = inputs.get("files", [])
    normalized: list[NormalizedFile] = []
    if not isinstance(raw_files, list):
        return normalized

    for group in raw_files:
        if not isinstance(group, Mapping):
            continue
        key = str(group.get("key", "file"))

        # Backward/third-party compatibility: some implementations send a single content field.
        if "contents" in group or "content" in group:
            normalized.append(
                NormalizedFile(
                    key=key,
                    filename=str(group.get("filename", "unknown")),
                    content_base64=str(group.get("contents") or group.get("content") or ""),
                )
            )

        files = group.get("files", [])
        if not isinstance(files, list):
            continue
        for f in files:
            if isinstance(f, Mapping):
                normalized.append(
                    NormalizedFile(
                        key=key,
                        filename=str(f.get("filename", "unknown")),
                        content_base64=str(f.get("content", "")),
                    )
                )
    return normalized


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4})(?!\d)")
MY_NUMBER_LIKE_RE = re.compile(r"(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)")
POSTAL_CODE_RE = re.compile(r"(?<!\d)\d{3}-\d{4}(?!\d)")


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: dict[str, int]


def redact_pii_with_counts(text: str) -> RedactionResult:
    counts: dict[str, int] = {}

    def sub(pattern: re.Pattern[str], label: str, value: str) -> str:
        matches = pattern.findall(value)
        counts[label] = len(matches)
        return pattern.sub(f"[REDACTED_{label}]", value)

    s = text
    # ID first to avoid partial phone matches.
    s = sub(MY_NUMBER_LIKE_RE, "ID", s)
    s = sub(EMAIL_RE, "EMAIL", s)
    s = sub(PHONE_RE, "PHONE", s)
    s = sub(POSTAL_CODE_RE, "POSTAL_CODE", s)
    return RedactionResult(text=s, counts={k: v for k, v in counts.items() if v})


def redact_pii(text: str) -> str:
    return redact_pii_with_counts(text).text


INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore (all )?(previous|above) instructions",
        r"system prompt",
        r"developer message",
        r"reveal .*prompt",
        r"命令を無視",
        r"以前の指示",
        r"システムプロンプト",
        r"開発者メッセージ",
    ]
]


@dataclass(frozen=True)
class SafetyFinding:
    kind: Literal["prompt_injection", "suspicious_input"]
    message: str
    severity: Literal["low", "medium", "high"] = "medium"


def detect_prompt_injection(text: str) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            findings.append(
                SafetyFinding(
                    kind="prompt_injection",
                    severity="high",
                    message="プロンプトインジェクションの可能性: 入力内に、AIへの指示を上書きしようとする文言が含まれている可能性があります。",
                )
            )
            break
    return findings


def markdown_report(title: str, sections: Iterable[tuple[str, str | list[str] | dict[str, Any]]]) -> str:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        if isinstance(body, list):
            lines.extend(f"- {item}" for item in (body or ["なし"]))
        elif isinstance(body, dict):
            if not body:
                lines.append("なし")
            else:
                lines.extend(f"- **{key}**: {value}" for key, value in body.items())
        else:
            lines.append(body or "なし")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def bullet_list(items: Iterable[str], *, empty: str = "なし") -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return empty
    return "\n".join(f"- {value}" for value in values)
