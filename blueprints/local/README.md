# Local Blueprint

This blueprint is for local demos and development.

## Components

- `easy_japanese_rewriter` on port `8000`
- `citizen_faq_rag` on port `8001`
- `gennai-local-runner` on port `8010`
- local JSONL traces under `reports/traces.jsonl`
- eval and operational reports under `reports/`

## Security baseline

- Keep endpoints on `127.0.0.1` during demos.
- Do not log raw citizen text, raw files, or raw model outputs.
- Use safe mode by default.
- Treat Local Runner as a developer tool, not a public web application.

## Commands

```bash
make install
make eval-report
make demo-traces
make ops-report
make run-faq-rag
make run-local-runner
```
