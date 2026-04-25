from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .catalog import build_default_inputs, load_catalog, repo_root_from
from .client import EndpointError, call_gennai_endpoint, export_curl_command, pretty_payload

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
except Exception:  # pragma: no cover
    FastAPI = None
    HTMLResponse = None
    JSONResponse = None

APP_VERSION = "0.7.0"


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
    header { background: linear-gradient(135deg, #111827, #1f2937); color: white; padding: 22px 28px; }
    header code { color: #d1fae5; }
    main { max-width: 1220px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: 390px 1fr; gap: 20px; }
    section, aside { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
    label { display: block; font-weight: 650; margin: 14px 0 6px; }
    small { color: #6b7280; display:block; margin-bottom: 5px; line-height: 1.45; }
    input, textarea, select { box-sizing: border-box; width: 100%; border: 1px solid #d1d5db; border-radius: 10px; padding: 10px 11px; font: inherit; background: white; }
    textarea { min-height: 112px; resize: vertical; }
    button { border: 0; border-radius: 999px; padding: 10px 16px; font-weight: 700; cursor: pointer; }
    button.primary { background: #111827; color: white; }
    button.secondary { background: #e5e7eb; color: #111827; }
    button.ghost { background: transparent; color: #374151; border: 1px solid #d1d5db; }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .pill { display: inline-block; background: #eef2ff; color: #3730a3; padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .muted { color: #6b7280; }
    .error { color: #b91c1c; font-weight: 700; }
    .grid-full { grid-column: 1 / -1; }
    .tabs { display:flex; gap:8px; margin: 12px 0; flex-wrap: wrap; }
    .tab { border-radius: 999px; padding: 8px 12px; background:#f3f4f6; color:#374151; }
    .tab.active { background:#111827; color:white; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #0b1020; color: #e5e7eb; padding: 16px; border-radius: 12px; min-height: 220px; }
    .preview { border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; min-height: 220px; background:#fff; line-height:1.65; }
    .preview h1 { font-size: 1.45rem; border-bottom:1px solid #e5e7eb; padding-bottom:8px; }
    .preview h2 { font-size: 1.15rem; margin-top:1.2rem; }
    .preview code { background:#f3f4f6; border-radius:4px; padding:1px 4px; }
    .preview ul { padding-left: 1.3rem; }
    .hidden { display:none; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<header>
  <div class="pill">v0.7 launch-ready developer experience</div>
  <h1>Gennai Local Runner</h1>
  <p>manifestからフォームを生成し、ファイル入力も含めてローカルの源内互換APIへPOSTし、<code>outputs</code> Markdownをプレビューします。</p>
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
  <section class="grid-full">
    <div class="row">
      <h2 style="margin-right:auto;">Request</h2>
      <button class="ghost" onclick="refreshRequestPreview()">payload更新</button>
      <button class="ghost" onclick="loadCurl()">curl生成</button>
    </div>
    <div class="tabs">
      <button class="tab active" id="tab-payload" onclick="showRequestTab('payload')">JSON payload</button>
      <button class="tab" id="tab-curl" onclick="showRequestTab('curl')">curl export</button>
    </div>
    <pre id="payloadPreview"></pre>
    <pre id="curlPreview" class="hidden"></pre>
  </section>
  <section class="grid-full">
    <div class="row">
      <h2 style="margin-right:auto;">Result</h2>
      <button class="ghost" onclick="copyResult()">結果をコピー</button>
    </div>
    <p id="status" class="muted">未実行</p>
    <div class="tabs">
      <button class="tab active" id="tab-preview" onclick="showResultTab('preview')">Markdown preview</button>
      <button class="tab" id="tab-raw" onclick="showResultTab('raw')">Raw outputs</button>
    </div>
    <div id="resultPreview" class="preview"></div>
    <pre id="resultRaw" class="hidden"></pre>
  </section>
</main>
<script>
let catalog = [];
let active = null;
let lastOutputs = '';

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
  refreshRequestPreview();
  document.getElementById('status').textContent = '未実行';
  setOutputs('');
}

function renderForm(format) {
  const form = document.getElementById('form');
  form.innerHTML = '';
  for (const [key, field] of Object.entries(format)) {
    if (field.type === 'hidden') continue;
    if (field.type === 'file') {
      const label = document.createElement('label');
      label.textContent = field.title || key;
      label.htmlFor = `field-${key}`;
      form.appendChild(label);
      if (field.desc) {
        const small = document.createElement('small');
        small.textContent = field.desc + ' Local Runner v0.7はテキスト系ファイルをbase64化してinputs.filesへ入れます。';
        form.appendChild(small);
      }
      const el = document.createElement('input');
      el.type = 'file';
      el.id = `field-${key}`;
      el.dataset.key = key;
      el.dataset.type = field.type;
      if (field.multiple) el.multiple = true;
      if (field.accept) el.accept = field.accept;
      el.addEventListener('change', refreshRequestPreview);
      form.appendChild(el);
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
    el.addEventListener('input', refreshRequestPreview);
    el.addEventListener('change', refreshRequestPreview);
    form.appendChild(el);
  }
}

function loadDefaults() {
  if (!active) return;
  renderForm(active.request_format);
  refreshRequestPreview();
  document.getElementById('status').textContent = 'デフォルト入力を復元しました';
}

async function collectPayload() {
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
    if (type === 'file') {
      const files = await filesToPayload(key, el.files || []);
      if (files.length) {
        if (!Array.isArray(inputs.files)) inputs.files = [];
        inputs.files.push({key, files});
      }
    } else if (type === 'number') inputs[key] = Number(el.value);
    else inputs[key] = el.value;
  }
  return { inputs };
}

async function refreshRequestPreview() {
  document.getElementById('payloadPreview').textContent = JSON.stringify(await collectPayload(), null, 2);
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function filesToPayload(key, fileList) {
  const files = [];
  for (const file of Array.from(fileList)) {
    files.push({filename: file.name, content: await fileToBase64(file)});
  }
  return files;
}

async function loadCurl() {
  await refreshRequestPreview();
  const payload = await collectPayload();
  const res = await fetch('/api/curl', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      endpoint: document.getElementById('endpoint').value,
      payload,
    }),
  });
  const body = await res.json();
  document.getElementById('curlPreview').textContent = body.curl || body.error || '';
  showRequestTab('curl');
}

async function runApp() {
  const status = document.getElementById('status');
  status.textContent = '実行中...';
  setOutputs('');
  await refreshRequestPreview();
  try {
    const payload = await collectPayload();
    const res = await fetch('/api/call', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        endpoint: document.getElementById('endpoint').value,
        payload,
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || 'request failed');
    status.textContent = '成功';
    setOutputs(body.outputs);
  } catch (e) {
    status.innerHTML = `<span class="error">失敗: ${escapeHtml(e.message)}</span>`;
  }
}

function setOutputs(text) {
  lastOutputs = text || '';
  document.getElementById('resultRaw').textContent = lastOutputs;
  document.getElementById('resultPreview').innerHTML = renderMarkdown(lastOutputs);
}

function showResultTab(which) {
  document.getElementById('tab-preview').classList.toggle('active', which === 'preview');
  document.getElementById('tab-raw').classList.toggle('active', which === 'raw');
  document.getElementById('resultPreview').classList.toggle('hidden', which !== 'preview');
  document.getElementById('resultRaw').classList.toggle('hidden', which !== 'raw');
}

function showRequestTab(which) {
  document.getElementById('tab-payload').classList.toggle('active', which === 'payload');
  document.getElementById('tab-curl').classList.toggle('active', which === 'curl');
  document.getElementById('payloadPreview').classList.toggle('hidden', which !== 'payload');
  document.getElementById('curlPreview').classList.toggle('hidden', which !== 'curl');
}

async function copyResult() {
  await navigator.clipboard.writeText(lastOutputs);
  document.getElementById('status').textContent = '結果をコピーしました';
}

function renderMarkdown(markdown) {
  if (!markdown) return '<p class="muted">結果はまだありません。</p>';
  const lines = String(markdown).split(/\r?\n/);
  let html = '';
  let inList = false;
  for (const line of lines) {
    if (line.startsWith('# ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h1>${inline(escapeHtml(line.slice(2)))}</h1>`;
    } else if (line.startsWith('## ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h2>${inline(escapeHtml(line.slice(3)))}</h2>`;
    } else if (line.startsWith('- ')) {
      if (!inList) { html += '<ul>'; inList = true; }
      html += `<li>${inline(escapeHtml(line.slice(2)))}</li>`;
    } else if (line.trim() === '') {
      if (inList) { html += '</ul>'; inList = false; }
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p>${inline(escapeHtml(line))}</p>`;
    }
  }
  if (inList) html += '</ul>';
  return html;
}

function inline(s) {
  return s
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+?)`/g, '<code>$1</code>');
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

    @app.post("/api/curl")
    def curl(payload: dict[str, Any]):
        try:
            endpoint = str(payload.get("endpoint", ""))
            request_payload = payload.get("payload")
            if not isinstance(request_payload, dict):
                return JSONResponse({"error": "`payload` must be an object"}, status_code=400)
            return {"curl": export_curl_command(endpoint, request_payload), "payload": pretty_payload(request_payload)}
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
