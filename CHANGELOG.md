# Changelog

## v0.4.0

- Added `gennai-local-runner`, a local browser UI that renders manifest-based forms and calls localhost Gennai-compatible endpoints.
- Added `gennai-red-team-lite` with prompt-injection, PII, and hallucination smoke tests.
- Upgraded `gennai-cli` to scaffold app, manifest, eval, and test files.
- Added pluggable Citizen FAQ RAG search backends: lexical, BM25, and hybrid.
- Added v0.4 tests for local runner, CLI scaffolding, search backends, and red-team runner.
- Updated CI, Makefile, docs, and README for the v0.4 developer experience.

## v0.3.0

- Added `citizen_faq_rag` as a grounded, evidence-first civic FAQ RAG app.
- Added dependency-free lexical retriever for local deterministic demos.
- Added sample municipal FAQ corpus with source IDs, departments, and freshness metadata.
- Added RAG manifest fields for sample corpus, answer style, safe mode, and max references.
- Added citizen FAQ eval cases for grounded answers, abstention, PII redaction, and prompt-injection handling.
- Added `make run-faq-rag` and `make eval-faq-rag`.


## v0.2.0

### Added

- Flagship `easy_japanese_rewriter` app with structured Markdown output
- Optional OpenAI-compatible LLM adapter with deterministic offline fallback
- PII redaction with counts
- Prompt-injection detection notes
- manifest JSON Schema and validation script
- YAML eval runner with contains / not-contains / regex assertions
- Dockerfile, Docker Compose, Makefile, and CI workflow
- engineering, compatibility, security, and launch-plan docs

### Improved

- `gennai_app_kit` now centralizes request parsing, checkbox parsing, file normalization, response creation, safety helpers, and LLM adapters
- `easy_japanese_rewriter` now includes a human review checklist and safer default behavior