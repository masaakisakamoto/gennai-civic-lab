# Citizen FAQ RAG indexing

v0.7 adds a dependency-free persistent BM25 index for `citizen_faq_rag`.

## Why this exists

The v0.3/v0.4 RAG flow searched the corpus in memory each time. That is fine for demos, but a serious public-sector AI project needs visible corpus versioning and repeatable retrieval artifacts.

The v0.7 index gives you:

- a stable corpus fingerprint
- a document count and source list
- precomputed BM25 term statistics
- a local JSON artifact that can be inspected and regenerated
- fallback behavior if an index is missing or stale

## Build the sample index

```bash
make build-faq-index
```

Output:

```text
.gennai/index/citizen_faq_bm25.json
```

`.gennai/` is ignored by Git. Do not commit indexes built from confidential or personal data.

## Use the index

In Local Runner, choose one of:

- `persistent_bm25`
- `hybrid_persistent`

Or set the path explicitly:

```bash
export GENNAI_FAQ_INDEX_PATH=.gennai/index/citizen_faq_bm25.json
make run-faq-rag
```

## Stale-index behavior

The backend compares the index corpus fingerprint with the current corpus fingerprint. If they do not match, it falls back to in-memory BM25 rather than failing the request.

This is deliberate: stale indexes should be visible and fixable, but the demo should remain usable.

## Production note

For production-like usage, keep the index build in CI/CD and treat corpus updates as versioned releases. Avoid indexing unreviewed data, personal data, or documents whose publication status is unclear.
