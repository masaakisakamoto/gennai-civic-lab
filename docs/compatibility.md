# Compatibility notes

This project targets Gennai-compatible external AI apps.

## Synchronous response

Apps return:

```json
{
  "outputs": "Markdown text"
}
```

## Request format manifest

Manifests in `manifests/*.gennai.json` define the fields shown to users when registering an AI app. Supported field families are:

- `text`
- `textarea`
- `number`
- `file`
- `select`
- `checkbox`
- `radio`
- `hidden`

## Request body

When a user executes an app, the values are sent under `inputs`:

```json
{
  "inputs": {
    "text": "...",
    "tone": "やさしい"
  }
}
```

## Files

Files are normalized through `normalize_files()`. The current implementation supports both grouped `files[]` and simpler `content`/`contents` variants for third-party mock compatibility.

## Caveat

The official API spec notes that it is experimental and may change. Keep this compatibility layer small so changes can be absorbed in `gennai_app_kit` instead of every app.
