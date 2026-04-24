from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    used_fallback: bool = False


class LLMClient(Protocol):
    def complete(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> LLMResult:
        ...


class OfflineLLMClient:
    """A deterministic client used for tests and local demos."""

    def __init__(self, response: str = "") -> None:
        self.response = response

    def complete(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> LLMResult:
        prompt_tail = messages[-1].content if messages else ""
        text = self.response or prompt_tail[:2000]
        return LLMResult(text=text, provider="offline", model="deterministic", used_fallback=True)


class OpenAICompatibleClient:
    """Tiny dependency-free client for OpenAI-compatible chat completion endpoints.

    Environment variables:
      - GENNAI_LLM_BASE_URL: e.g. https://api.example.com/v1
      - GENNAI_LLM_API_KEY
      - GENNAI_LLM_MODEL
    """

    def __init__(self, *, base_url: str, api_key: str, model: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> LLMResult:
        payload = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:  # nosec B310 - user supplied endpoint for local OSS adapter
                body = json.loads(res.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response did not include choices")
        message = choices[0].get("message") or {}
        text = message.get("content")
        if not isinstance(text, str):
            raise RuntimeError("LLM response did not include message.content")
        return LLMResult(text=text, provider="openai_compatible", model=self.model)


def llm_from_env(*, fallback_response: str = "") -> LLMClient:
    provider = os.environ.get("GENNAI_LLM_PROVIDER", "offline").strip().lower()
    if provider in {"openai_compatible", "openai-compatible", "openai"}:
        base_url = os.environ.get("GENNAI_LLM_BASE_URL", "").strip()
        api_key = os.environ.get("GENNAI_LLM_API_KEY", "").strip()
        model = os.environ.get("GENNAI_LLM_MODEL", "").strip()
        if base_url and api_key and model:
            return OpenAICompatibleClient(base_url=base_url, api_key=api_key, model=model)
    return OfflineLLMClient(fallback_response)
