# Docker Compose Blueprint

This blueprint shows how to run the civic AI app stack locally with separate services.
It is intentionally conservative: localhost bindings, no public exposure, and no secrets in compose files.

## Services

- `easy-japanese`: Gennai-compatible API on `127.0.0.1:8000`
- `faq-rag`: Gennai-compatible API on `127.0.0.1:8001`
- `local-runner`: browser UI on `127.0.0.1:8010`

## PII and logging policy

- Do not log raw citizen questions or raw uploaded documents.
- Use `gennai_app_kit.audit` and `gennai_observability` for metadata-first records.
- Mount `reports/` only for local demo artifacts.

## Production note

This compose file is a development blueprint, not a production deployment. For production,
put the APIs behind a private network, add authentication, set resource limits, and forward
metadata-only traces to your approved logging system.

## Run

```bash
docker compose -f blueprints/docker-compose/docker-compose.full.yml up --build
```
