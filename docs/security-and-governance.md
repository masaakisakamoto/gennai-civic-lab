# Security and governance

This project is designed for civic AI prototypes and compatibility experiments. Production use requires organizational review.

## Default safeguards

- PII-like strings are masked by default in `easy_japanese_rewriter` safe mode.
- Prompt-injection-like strings are detected and surfaced as safety notes.
- Outputs include a human review checklist.
- LLM mode is optional; deterministic fallback enables local testing without sending data to an external provider.

## Never do this

- Do not upload confidential documents to an external LLM without approval.
- Do not treat model output as legal advice.
- Do not remove human review for public notices, policy decisions, eligibility decisions, or legal/ordinance text.
- Do not log raw personal data in production.

## Production checklist

| Area | Check |
|---|---|
| Data | Classification and retention policy |
| LLM | Provider approval and regional/data processing requirements |
| Logs | PII redaction and access control |
| Review | Human approval workflow |
| Evals | Regression cases for important document types |
| Incidents | Security contact and disclosure flow |

## Disclosure

Use `SECURITY.md` for vulnerability reports. For official Gennai repositories, follow the official security disclosure process instead of reporting through this unofficial project.


## RAG-specific safeguards

`citizen_faq_rag` treats every question and reference document as untrusted input.
It searches the corpus, surfaces source IDs and excerpts, and abstains when the evidence is weak.
For production use, add these controls before using real municipal data:

- Use only official, reviewed, versioned source documents.
- Store document freshness metadata such as last-reviewed date and owning department.
- Keep answer generation grounded to retrieved passages.
- Evaluate both answerable questions and intentionally unanswerable questions.
- Log source IDs and confidence signals, not raw personal data.
- Define a human review flow for policy-sensitive or legally sensitive responses.


## v0.4 red-team smoke tests

Run:

```bash
make red-team
```

Current smoke cases verify:

- safe-mode PII redaction
- unsupported FAQ questions abstain instead of hallucinating
- prompt-injection text is detected and treated as user/source text

These checks are intentionally small and deterministic. They should be expanded before any production or municipality-facing deployment.

## Local runner endpoint policy

`gennai-local-runner` only calls `http://127.0.0.1:*` and `http://localhost:*` by default. This avoids accidental remote submission during demos.
