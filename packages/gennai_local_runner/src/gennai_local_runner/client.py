from __future__ import annotations

import json
import shlex
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EndpointError(Exception):
    message: str
    status: int | None = None

    def __str__(self) -> str:
        return self.message


def _validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise EndpointError("endpoint URL is required")
    if not (url.startswith("http://127.0.0.1:") or url.startswith("http://localhost:")):
        raise EndpointError(
            "local runner only calls localhost endpoints by default. "
            "Use an explicit reverse proxy or extend this policy for remote demos."
        )
    return url


def pretty_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def export_curl_command(url: str, payload: dict[str, Any]) -> str:
    """Create a reproducible curl command for a local Gennai-compatible call."""

    endpoint = _validate_url(url)
    body = pretty_payload(payload)
    return " \\\n  ".join(
        [
            f"curl -X POST {shlex.quote(endpoint)}",
            "-H 'Content-Type: application/json'",
            f"-d {shlex.quote(body)}",
        ]
    )


def call_gennai_endpoint(url: str, payload: dict[str, Any], *, timeout: float = 30.0) -> dict[str, str]:
    """Call a Gennai-compatible app endpoint and validate the synchronous output shape."""

    endpoint = _validate_url(url)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - localhost-only policy
            body = response.read().decode("utf-8")
            decoded = json.loads(body)
    except urllib.error.HTTPError as e:
        raise EndpointError(f"endpoint returned HTTP {e.code}", status=e.code) from e
    except urllib.error.URLError as e:
        raise EndpointError(f"could not connect to endpoint: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise EndpointError("endpoint did not return valid JSON") from e

    if not isinstance(decoded, dict) or not isinstance(decoded.get("outputs"), str):
        raise EndpointError("endpoint response must be an object with a string 'outputs' field")
    return {"outputs": decoded["outputs"]}
