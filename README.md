# gennai-civic-lab

[![CI](https://github.com/YOUR_NAME/gennai-civic-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_NAME/gennai-civic-lab/actions/workflows/ci.yml)

**源内互換の自治体・行政AIアプリを、誰でも作れる・試せる・評価できる非公式OSSラボ**です。

> This project is an unofficial community project. It is not affiliated with, endorsed by, or maintained by the Digital Agency of Japan.

## Why this exists

源内Webは、行政実務用AIアプリとして外部REST APIを呼び出せます。つまり、公式本体に変更を入れなくても、互換プロトコルに合わせた外部AIアプリ・SDK・評価基盤・デプロイ雛形をOSSとして育てられます。

このリポジトリは、単なるサンプル集ではなく、**公共領域で使うAIアプリに必要な品質の型**をまとめることを狙っています。

- `inputs` / `outputs` 互換のAPI設計
- 行政・自治体向けAIアプリの実装例
- LLMプロバイダーを差し替えられる抽象化
- ルールベースfallbackによるローカルデモ
- PIIマスキング、プロンプトインジェクション検知、監査ログの雛形
- YAML評価ケースによる回帰テスト（easy Japanese + Citizen FAQ RAG）
- v0.4 local runner UIによるブラウザ上の開発体験
- v0.4 red-team smoke testsによる最低限の安全性回帰テスト
- manifest JSON Schemaと検証CLI
- Docker / CI / Makefile / ドキュメント

## Repository map

```text
apps/                         # 源内互換AIアプリの実装例
  easy_japanese_rewriter/      # v0.2 flagship app
  meeting_summary/
  citizen_faq_rag/              # v0.3 grounded FAQ RAG app
  sports_promotion_advisor/
  policy_briefing/
  ordinance_checklist/

packages/
  gennai_app_kit/              # Python SDK: request/response, guardrails, LLM adapter
  gennai_evals/                # YAML eval runner
  gennai_cli/                  # app scaffold CLI
  gennai_local_runner/         # v0.4 local browser UI for manifests and endpoints
  gennai_form_spec/            # manifest JSON Schema
  gennai_red_team_lite/        # v0.4 prompt-injection / PII / hallucination smoke tests

manifests/                     # 源内Webに登録するリクエスト形式JSON例
evals/                         # 評価ケース
docs/                          # 設計・セキュリティ・OSS戦略
tests/                         # unit tests
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e packages/gennai_app_kit
pip install -e packages/gennai_evals
pip install fastapi uvicorn pytest pyyaml jsonschema
```

### Run the flagship app

```bash
uvicorn apps.easy_japanese_rewriter.app:app --reload --port 8000
```

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {
      "text": "本制度の利用に際しては、所定の申請書類を提出してください。詳細は担当課へお問い合わせください。",
      "audience": "市民向け",
      "tone": "やさしい",
      "mode": "safe"
    }
  }'
```

The response is compatible with the synchronous Gennai app contract:

```json
{
  "outputs": "# やさしい日本語への書き換え\n..."
}
```


### Run the Citizen FAQ RAG app

```bash
make run-faq-rag
```

```bash
curl -X POST http://127.0.0.1:8001/ \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {
      "question": "子ども医療費助成の申請に必要なものを教えてください",
      "use_sample_corpus": "yes",
      "answer_style": "市民向け",
      "mode": "safe",
      "max_results": 3
    }
  }'
```

v0.3 adds a deterministic, evidence-first RAG app for civic FAQ and procedure guidance. It returns references, excerpts, safety notes, and abstains when the evidence is weak.


### Run the local browser runner

v0.4 adds a local UI that reads `manifests/*.gennai.json`, renders an input form, calls a local Gennai-compatible endpoint, and displays the returned Markdown.

Terminal A:

```bash
make run-faq-rag
```

Terminal B:

```bash
make run-local-runner
```

Open:

```text
http://127.0.0.1:8010/
```

### Run red-team smoke tests

```bash
make red-team
```

The red-team smoke suite checks that the apps do not treat prompt-injection text as instructions, redact common PII in safe mode, and abstain when FAQ evidence is weak.


### Optional LLM mode

The app works offline with deterministic fallback rules. To use an OpenAI-compatible chat completion endpoint, set:

```bash
export GENNAI_LLM_PROVIDER=openai_compatible
export GENNAI_LLM_BASE_URL=https://api.example.com/v1
export GENNAI_LLM_API_KEY=...
export GENNAI_LLM_MODEL=your-model
```

No API key is required for tests or local demos.

## What to publish first

Start with this monorepo as **`gennai-civic-lab`**. After traction, split into:

| Repo | Purpose |
|---|---|
| `gennai-app-kit` | SDK for Gennai-compatible AI apps |
| `gennai-civic-apps` | Civic and municipal AI app catalog |
| `gennai-evals` | Eval and regression testing harness |
| `gennai-form-spec` | Manifest JSON Schema and validation tools |
| `gennai-local-runner` | Local testing UI/mock runner |
| `gennai-blueprints` | AWS/Azure/GCP deployment templates |

## Quality bar

This project treats public-sector AI apps as production software, not prompt demos.

```text
Typed request parsing
Deterministic fallback
LLM abstraction
Structured Markdown output
Tests and evals
Security notes
PII handling
Prompt-injection checks
Manifest schema validation
Clear unofficial status
```

## License

MIT License. See `LICENSE`.

## Caution

When handling administrative documents, personal information, confidential information, or legally sensitive text, follow your organization’s rules, applicable laws, security policies, and AI usage guidelines. This OSS is a development aid, not a legal or policy decision maker.
