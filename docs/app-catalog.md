# Civic AI app catalog

| App | Description | First production concern |
|---|---|---|
| `easy_japanese_rewriter` | 行政文をやさしい日本語へ変換 | 意味の改変防止、担当者確認 |
| `meeting_summary` | 会議メモから決定事項・ToDo・リスク抽出 | 発言者・決定事項の誤認防止 |
| `citizen_faq_rag` | 市民FAQ・手続き案内向けの根拠提示RAG | 参照元・更新日・回答不能時の扱い |
| `sports_promotion_advisor` | 地域スポーツ施策の企画支援 | 地域実情への適合、KPI設計 |
| `policy_briefing` | 政策資料の論点整理 | 政策判断の過度な自動化防止 |
| `ordinance_checklist` | 条例・要綱チェック補助 | 法的判断は専門職レビュー必須 |

## Recommended first demo

`easy_japanese_rewriter` is the best first app because it is:

- easy to understand
- low dependency
- public-sector relevant
- testable without private data
- useful for accessibility and civic communication


## v0.3 focus: Citizen FAQ RAG

`citizen_faq_rag` is the second flagship app after `easy_japanese_rewriter`.
It demonstrates the public-sector AI quality bar more clearly than a prompt-only app:

- evidence-first answers
- source IDs and excerpts
- deterministic retrieval without external API keys
- abstention when evidence is weak
- PII redaction for demo/public review
- prompt-injection detection
- eval cases for both answerable and unanswerable questions

Recommended demo question:

```text
子ども医療費助成の申請に必要なものを教えてください
```


## v0.4 Developer tools

| Tool | Purpose |
|---|---|
| `gennai-local-runner` | manifestからフォームを生成し、ローカルAPIにPOSTして結果を確認する |
| `gennai-cli` | 新しい源内互換アプリのapp/manifest/eval/testを生成する |
| `gennai-red-team-lite` | prompt injection / PII / 根拠なし回答のsmoke testを実行する |
