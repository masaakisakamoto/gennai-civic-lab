from apps.citizen_faq_rag.search_backends import (
    BM25SearchBackend,
    HybridSearchBackend,
    LexicalSearchBackend,
    get_search_backend,
)


def test_backend_factory_defaults_to_lexical() -> None:
    assert get_search_backend("unknown").name == "lexical"
    assert get_search_backend("bm25").name == "bm25"
    assert get_search_backend("hybrid").name == "hybrid"


def test_backend_names_are_stable() -> None:
    assert LexicalSearchBackend().name == "lexical"
    assert BM25SearchBackend().name == "bm25"
    assert HybridSearchBackend().name == "hybrid"
