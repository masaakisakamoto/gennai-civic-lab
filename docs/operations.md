# Operations Guide

v0.6 adds a lightweight operational layer for Gennai-compatible civic AI apps.

## Operating principles

1. **Metadata over raw data**: traces should not contain raw citizen text or raw documents.
2. **Evidence before promotion**: run eval, red-team, and ops reports before release.
3. **Small replaceable pieces**: JSONL tracing can later be replaced by OpenTelemetry.
4. **Private by default**: Local Runner and internal APIs should not be publicly exposed.

## Standard quality gate

```bash
make test
make validate-manifests
make eval
make red-team
make eval-report
make demo-traces
make ops-report
```

Generated artifacts:

```text
reports/eval-report.md
reports/eval-report.json
reports/traces.jsonl
reports/ops-report.md
reports/ops-report.json
```

## What to inspect

- Eval failures must be zero.
- Red-team failures must be zero.
- Trace errors should be zero for demos.
- Metrics should show request counts and request duration by app.
- Reports should not include raw citizen text.
