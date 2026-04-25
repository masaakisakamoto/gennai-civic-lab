from pathlib import Path

from apps.citizen_faq_rag.indexing import (
    build_index_from_corpus_files,
    fingerprint_documents,
    is_index_current,
    load_index,
    save_index,
    search_index,
)
from apps.citizen_faq_rag.retriever import build_documents, load_corpus_text
from apps.citizen_faq_rag.search_backends import PersistentBM25SearchBackend, get_search_backend

SAMPLE = Path("apps/citizen_faq_rag/corpus/sample_faq.md")


def test_persistent_bm25_index_roundtrip(tmp_path):
    docs = build_documents([("sample_faq.md", load_corpus_text(SAMPLE))])
    index = build_index_from_corpus_files([SAMPLE], corpus_id="test_faq")
    path = tmp_path / "faq_index.json"
    save_index(index, path)

    loaded = load_index(path)
    assert loaded.schema_version == "gennai.faq_bm25_index.v1"
    assert loaded.corpus_version.document_count == len(docs)
    assert loaded.corpus_version.corpus_fingerprint == fingerprint_documents(docs)
    assert is_index_current(loaded, docs)

    hits = search_index(loaded, "子ども医療費助成の申請に必要なもの", limit=3)
    assert hits
    assert hits[0].doc.id == "FAQ-001"


def test_persistent_bm25_backend_uses_index_when_current(tmp_path, monkeypatch):
    docs = build_documents([("sample_faq.md", load_corpus_text(SAMPLE))])
    index = build_index_from_corpus_files([SAMPLE], corpus_id="test_faq")
    path = tmp_path / "faq_index.json"
    save_index(index, path)
    monkeypatch.setenv("GENNAI_FAQ_INDEX_PATH", str(path))

    backend = PersistentBM25SearchBackend()
    hits = backend.search("体育館の予約方法", docs, limit=3)
    assert hits
    assert hits[0].doc.id == "FAQ-003"


def test_get_search_backend_accepts_persistent_modes():
    assert get_search_backend("persistent_bm25").name == "persistent_bm25"
    assert get_search_backend("hybrid_persistent").name == "hybrid_persistent"
