# OSS project roadmap

## North star

Build the most developer-friendly unofficial ecosystem for Gennai-compatible civic AI apps.

## Project ideas

| Priority | Project | Description | Proof of skill |
|---:|---|---|---|
| 1 | `gennai-app-kit` | Python SDK for compatible apps | API design, typing, safety helpers |
| 2 | `gennai-civic-apps` | Civic app catalog | domain modeling, usable demos |
| 3 | `gennai-evals` | YAML regression/eval runner | LLMOps, quality engineering |
| 4 | `gennai-form-spec` | JSON Schema for manifests | contract-first development |
| 5 | `gennai-local-runner` | local UI/mock runner | DX, frontend/backend integration |
| 6 | `gennai-pii-redactor-ja` | Japanese PII masking | security/privacy engineering |
| 7 | `gennai-redteam-lite` | prompt injection test pack | AI safety engineering |
| 8 | `gennai-rag-blueprint` | citizen FAQ RAG template | retrieval, citations, grounding |
| 9 | `gennai-observability` | logging/metrics/tracing kit | production operations |
| 10 | `awesome-gennai-ecosystem` | curated links and examples | community leadership |

## Immediate issues to create on GitHub

1. `easy_japanese_rewriter`: improve examples with 10 real-looking synthetic admin notices
2. `gennai_form_spec`: add TypeScript type generation
3. `gennai_evals`: add scoring mode and snapshot output
4. `gennai_app_kit`: add async job adapter
5. `citizen_faq_rag`: add source citation format
6. `docs`: add deployment guide for a small municipal PoC

## Demo narrative

> I noticed the official Gennai repositories do not currently accept feature PRs, so I built an unofficial compatibility ecosystem: SDK, manifests, evals, safety helpers, and civic AI app examples. The goal is not to fork the government system, but to make external compatible apps easier to build and evaluate.
