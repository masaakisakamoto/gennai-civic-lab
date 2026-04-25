from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from .catalog import build_default_inputs, load_catalog, repo_root_from
from .client import EndpointError, call_gennai_endpoint

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
except Exception:  # pragma: no cover
    FastAPI = None
    HTMLResponse = None
    JSONResponse = None

APP_VERSION = "0.4.0"


HTML = r"""
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>Gennai Local Runner</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root { color-scheme: light; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f7f7f8; color: #1f2937; }
    header { background: #111827; color: white; padding: 22px 28px; }
    main { max-width: 1180px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: 390px 1fr; gap: 20px; }
    section, aside { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
    label { display: block; font-weight: 650; margin: 14px 0 6px; }
    small { color: #6b7280; display:block; margin-bottom: 5px; line-height: 1.45; }
    input, textarea, select { box-sizing: border-box; width: 100%; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 11px; font: inherit; background: white; }
    textarea { min-height: 110px; resize: vertical; }
    button { border: 0; border-radius: 999px; padding: 10px 16px; font-weight: 700; cursor: pointer; }
    button.primary { background: #111827; color: white; }
    button.secondary { background: #e5e7eb; color: #111827; }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .pill { display: inline-block; background: #eef2ff; color: #3730a3; padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #0b1020; color: #e5e7eb; padding: 16px; border-radius: 12px; min-height: 260px; }
    .muted { color: #6b7280; }
    .error { color: #b91c1c; font-weight: 700; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<header>
  <div class="pill">v0.4 local DX</div>
  <h1>Gennai Local Runner</h1>
  <p>manifestを読み込み、ローカルの源内互換APIへPOSTして、<code>outputs</code> Markdownを確認する開発用UIです。</p>
</header>
<main>
  <aside>
    <h2>App</h2>
    <label for="appSelect">manifest</label>
    <select id="appSelect"></select>
    <label for="endpoint">endpoint</label>
    <input id="endpoint" />
    <div class="row" style="margin-top:14px;">
      <button class="secondary" onclick="loadDefaults()">デフォルト入力</button>
      <button class="primary" onclick="runApp()">実行</button>
    </div>
    <p class="muted">先に対象アプリを <code>make run-easy-ja</code> または <code>make run-faq-rag</code> で起動してください。</p>
  </aside>
  <section>
    <h2>Inputs</h2>
    <div id="form"></div>
  </section>
  <section style="grid-column: 1 / -1;">
    <h2>Result</h2>
    <p id="status" class="muted">未実行</p>
    <pre id="result"></pre>
  </section>
</main>
<script>
let catalog = [];
let active = null;

async function init() {
  const res = await fetch('/api/catalog');
  catalog = await res.json();
  const select = document.getElementById('appSelect');
  for (const item of catalog) {
    const option = document.createElement('option');
    option.value = item.app_id;
    option.textContent = `${item.title} (${item.manifest_path})`;
    select.appendChild(option);
  }
  select.addEventListener('change', () => selectApp(select.value));
  if (catalog.length) selectApp(catalog[0].app_id);
}

function fieldDefault(field, key) {
  if ('default_value' in field) return field.default_value;
  if (field.type === 'number') return field.min ?? 1;
  if (field.type === 'textarea' && key === 'question') return '子ども医療費助成の申請に必要なものを教えてください';
  if (field.type === 'textarea' && key === 'text') return '本制度の利用に際しては、所定の申請書類を提出してください。';
  if (['select','radio','checkbox'].includes(field.type) && field.items?.length) return field.items[0].value;
  return '';
}

function selectApp(appId) {
  active = catalog.find(x => x.app_id === appId);
  document.getElementById('endpoint').value = active.endpoint;
  renderForm(active.request_format);
}

function renderForm(format) {
  const form = document.getElementById('form');
  form.innerHTML = '';
  for (const [key, field] of Object.entries(format)) {
    if (field.type === 'hidden') continue;
    if (field.type === 'file') {
      const p = document.createElement('p');
      p.className = 'muted';
      p.innerHTML = `<strong>${escapeHtml(field.title || key)}</strong><br>v0.4 runnerではファイルアップロードは未対応です。textareaに貼り付けて検証してください。`;
      form.appendChild(p);
      continue;
    }
    const label = document.createElement('label');
    label.textContent = field.title || key;
    label.htmlFor = `field-${key}`;
    form.appendChild(label);
    if (field.desc) {
      const small = document.createElement('small');
      small.textContent = field.desc;
      form.appendChild(small);
    }

    let el;
    if (field.type === 'textarea') {
      el = document.createElement('textarea');
    } else if (field.type === 'select' || field.type === 'radio' || field.type === 'checkbox') {
      el = document.createElement('select');
      for (const item of (field.items || [])) {
        const option = document.createElement('option');
        option.value = item.value;
        option.textContent = item.title;
        el.appendChild(option);
      }
    } else {
      el = document.createElement('input');
      el.type = field.type === 'number' ? 'number' : 'text';
      if (field.min !== undefined) el.min = field.min;
      if (field.max !== undefined) el.max = field.max;
    }
    el.id = `field-${key}`;
    el.dataset.key = key;
    el.dataset.type = field.type;
    el.value = fieldDefault(field, key);
    form.appendChild(el);
  }
}

function loadDefaults() {
  if (!active) return;
  renderForm(active.request_format);
  document.getElementById('status').textContent = 'デフォルト入力を復元しました';
}

function collectPayload() {
  const inputs = {};
  for (const [key, field] of Object.entries(active.request_format)) {
    if (field.type === 'hidden') {
      inputs[key] = field.default_value ?? '';
      continue;
    }
  }
  for (const el of document.querySelectorAll('[data-key]')) {
    const key = el.dataset.key;
    const type = el.dataset.type;
    if (type === 'number') inputs[key] = Number(el.value);
    else inputs[key] = el.value;
  }
  return { inputs };
}

async function runApp() {
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  status.textContent = '実行中...';
  result.textContent = '';
  try {
    const res = await fetch('/api/call', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        endpoint: document.getElementById('endpoint').value,
        payload: collectPayload(),
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || 'request failed');
    status.textContent = '成功';
    result.textContent = body.outputs;
  } catch (e) {
    status.innerHTML = `<span class="error">失敗: ${escapeHtml(e.message)}</span>`;
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

init();
</script>
</body>
</html>
"""


def create_app(repo_root: Path | None = None):
    if FastAPI is None:  # pragma: no cover
        raise RuntimeError("fastapi is required for gennai-local-runner")

    root = repo_root or repo_root_from()
    app = FastAPI(title="gennai-local-runner", version=APP_VERSION)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(HTML)

    @app.get("/api/catalog")
    def catalog():
        return [
            {
                "app_id": item.app_id,
                "title": item.title,
                "manifest_path": item.manifest_path,
                "endpoint": item.endpoint,
                "request_format": item.request_format,
                "default_inputs": build_default_inputs(item.request_format),
            }
            for item in load_catalog(root)
        ]

    @app.post("/api/call")
    def call(payload: dict[str, Any]):
        try:
            endpoint = str(payload.get("endpoint", ""))
            request_payload = payload.get("payload")
            if not isinstance(request_payload, dict):
                return JSONResponse({"error": "`payload` must be an object"}, status_code=400)
            return call_gennai_endpoint(endpoint, request_payload)
        except EndpointError as e:
            return JSONResponse({"error": str(e), "status": e.status}, status_code=400)

    return app


app = create_app()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local browser UI for Gennai-compatible apps")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8010, type=int)
    args = parser.parse_args(argv)

    import uvicorn

    uvicorn.run("gennai_local_runner.app:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
