# gennai-local-runner

Local browser UI for Gennai-compatible AI apps.

## v0.5 features

- reads `manifests/*.gennai.json`
- generates input forms
- calls localhost-only compatible endpoints
- previews the exact JSON payload
- exports a reproducible curl command
- renders `outputs` as Markdown preview
- keeps raw Markdown visible for debugging

## Run

```bash
make run-faq-rag
make run-local-runner
```

Open:

```text
http://127.0.0.1:8010/
```


## v0.7

Local Runner can now encode text-like file inputs into `inputs.files`, preview the JSON payload, and export a matching curl command.
