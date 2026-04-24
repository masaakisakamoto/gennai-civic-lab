# gennai-app-kit

Python SDK for building Gennai-compatible civic AI apps.

## Features

- Parse `inputs` safely
- Return synchronous `{ "outputs": "Markdown" }` responses
- Normalize checkbox and file inputs
- Redact common Japanese PII patterns
- Detect simple prompt-injection attempts
- Use a dependency-free OpenAI-compatible LLM adapter
- Keep deterministic offline fallback for tests and demos

## Minimal app

```python
from gennai_app_kit import parse_request, output

def handle(payload: dict) -> dict[str, str]:
    ctx = parse_request(payload)
    return output(f"# Result\n\n{ctx.inputs['question']}")
```
