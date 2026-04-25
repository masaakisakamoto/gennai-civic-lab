# gennai-observability

Dependency-free observability primitives for Gennai-compatible civic AI apps.

## Why this exists

Public-sector AI needs operational evidence without leaking sensitive citizen text.
This package focuses on metadata-first tracing:

- request duration
- app/version/request identifiers
- status
- safe metadata
- event names and counts
- eval + trace operational reports

It intentionally avoids storing raw prompts, raw documents, or raw outputs.

## Example

```python
from gennai_observability import JsonlTraceExporter, TraceEvent, traced_call

exporter = JsonlTraceExporter("reports/traces.jsonl")
result, span = traced_call(
    lambda: {"outputs": "ok"},
    app_id="citizen_faq_rag",
    app_version="0.6.0",
    exporter=exporter,
    events=[TraceEvent("retrieval.completed", metadata={"backend": "hybrid", "hits": 3})],
)
```

Generate an operational report:

```bash
gennai-ops-report \
  --eval-json reports/eval-report.json \
  --traces-jsonl reports/traces.jsonl \
  --markdown-report reports/ops-report.md \
  --json-report reports/ops-report.json
```
