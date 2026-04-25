# v0.7 Release & Launch Plan

`gennai-civic-lab` v0.7 is the first release intended to be credible for external announcement.
It combines technical improvements with a launch kit so the project can be explained quickly on GitHub, X, Instagram, and in civic-tech conversations.

## What changed in v0.7

- Persistent BM25 index for `citizen_faq_rag`
- Corpus versioning through stable fingerprints
- `build-faq-index` Make target
- Local Runner file input support for text-like files
- Release readiness report
- Social launch templates for X and Instagram

## Release gate

Before posting publicly, run:

```bash
make test
make validate-manifests
make eval
make red-team
make ops-report
make build-faq-index
make release-readiness
```

For the Docker blueprint:

```bash
docker compose -f blueprints/docker-compose/docker-compose.full.yml up --build
```

Then check:

```bash
curl http://127.0.0.1:8001/healthz
curl http://127.0.0.1:8000/healthz
```

## Announcement sequence

1. Tag `v0.7.0` on GitHub.
2. Publish a short X post with the GitHub URL.
3. Follow with a technical X thread explaining the architecture.
4. Publish an Instagram carousel aimed at non-engineers and civic-tech people.
5. Reply to comments with concrete screenshots, demo commands, and the Local Runner URL.

## Positioning

This is not an official Digital Agency project. It is an unofficial, Gennai-compatible civic AI lab designed to explore safe, testable, and operationally ready AI apps for local-government workflows.
