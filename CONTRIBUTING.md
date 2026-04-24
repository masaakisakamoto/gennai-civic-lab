# Contributing

This is an unofficial community project.

## Quality expectations

- Keep the Gennai-compatible wire contract small: `inputs` in, `outputs` out.
- Add tests for every app behavior that matters.
- Add eval cases for generated-output expectations.
- Avoid committing secrets, real personal data, or confidential government documents.
- Make safety behavior visible in the app output.

## Development

```bash
make install
make test
make validate-manifests
make eval
```

## New app checklist

- `apps/<app_name>/app.py`
- `apps/<app_name>/README.md`
- `manifests/<app_name>.gennai.json`
- `evals/<app_name>.yaml`
- unit tests
- security notes if the app touches sensitive data
