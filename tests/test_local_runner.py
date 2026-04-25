from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from gennai_local_runner.catalog import build_default_inputs, default_endpoint, load_catalog
from gennai_local_runner.client import EndpointError, call_gennai_endpoint, export_curl_command, pretty_payload


def test_load_catalog_contains_manifest_apps() -> None:
    items = load_catalog(ROOT)
    ids = {item.app_id for item in items}
    assert "easy_japanese_rewriter" in ids
    assert "citizen_faq_rag" in ids


def test_build_default_inputs_for_question_manifest() -> None:
    item = next(item for item in load_catalog(ROOT) if item.app_id == "citizen_faq_rag")
    payload = build_default_inputs(item.request_format)
    assert "question" in payload
    assert payload["use_sample_corpus"] == "yes"
    assert payload["retrieval_backend"] == "lexical"


def test_default_endpoint_uses_known_ports() -> None:
    assert default_endpoint("easy_japanese_rewriter").endswith(":8000/")
    assert default_endpoint("citizen_faq_rag").endswith(":8001/")


def test_client_rejects_remote_url() -> None:
    with pytest.raises(EndpointError):
        call_gennai_endpoint("https://example.com/", {"inputs": {}})


def test_export_curl_command_for_local_endpoint() -> None:
    payload = {"inputs": {"question": "子ども医療費助成"}}
    command = export_curl_command("http://127.0.0.1:8001/", payload)
    assert "curl -X POST" in command
    assert "Content-Type: application/json" in command
    assert "子ども医療費助成" in command


def test_pretty_payload_is_stable_json() -> None:
    payload = {"inputs": {"b": 2, "a": 1}}
    rendered = pretty_payload(payload)
    assert rendered.index('"a"') < rendered.index('"b"')
