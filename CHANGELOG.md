# Changelog

## v0.6.0

### Added

- `gennai_observability` package for metadata-first tracing, metrics summaries, and operational reports.
- `make demo-traces` and `make ops-report`.
- `scripts/generate_demo_traces.py` and `scripts/generate_ops_report.py`.
- Deployment blueprints for local, Docker Compose, AWS, and Azure.
- `docs/operations.md` and `docs/v0.6-implementation-notes.md`.
- README operational report diagram.

### Design notes

- Observability remains dependency-free and PII-conscious.
- Demo traces store app/version/status/duration and safe metadata, not raw citizen text.
- Blueprints are conservative references, not production one-click automation.


## v0.5.0

- Upgraded `gennai-local-runner` with Markdown preview, raw outputs tab, payload preview, and curl export.
- Added eval report generation via `--markdown-report`, `--json-report`, and `make eval-report`.
- Added `scripts/import_faq_corpus.py` for CSV/JSONL to Markdown FAQ corpus import.
- Added PII-conscious audit primitives to `gennai_app_kit`.
- Added illustrative Local Runner asset and v0.5 implementation notes.
- Added tests for audit events, eval reports, curl export, and FAQ corpus import.


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