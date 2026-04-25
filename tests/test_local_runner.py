from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from gennai_local_runner.catalog import build_default_inputs, default_endpoint, load_catalog
from gennai_local_runner.client import EndpointError, call_gennai_endpoint


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
