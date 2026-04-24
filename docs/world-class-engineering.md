# World-class engineering bar for Gennai-compatible OSS

このOSSで見せたい技術力は「LLMアプリを作れる」ではありません。公共領域で使えるAIソフトウェアとして、設計・品質・安全性・運用まで見えていることです。

## 1. Contract-first

源内互換の最重要点は、外部REST APIとして受け取り、`inputs` を処理し、同期処理では `outputs` を返すことです。

このリポジトリでは、アプリごとの実装ではなく `gennai_app_kit` に以下を集約します。

- `parse_request()`
- `require_text()`
- `get_choice()`
- `normalize_files()`
- `output()`
- manifest builder / schema

## 2. Deterministic fallback

AIアプリはAPIキーがないと動かない、ではOSSとして弱いです。

そのため、旗艦アプリ `easy_japanese_rewriter` は以下の2系統を持ちます。

- LLM設定あり: OpenAI-compatible endpointを利用
- LLM設定なし: ルールベースfallbackでデモ・テスト・評価が可能

## 3. Safety by default

公共領域では、便利さよりも安全性の初期値が大事です。

- PIIらしき文字列をデフォルトでマスク
- プロンプトインジェクションらしき文言を検知
- 生成結果に「担当者確認チェック」を必ず出す
- 法的・制度的判断をAIだけで確定しない

## 4. Evals, not vibes

生成AIアプリの品質は、プロンプトの雰囲気ではなく回帰テストで示します。

`evals/*.yaml` に以下を書くことで、README上でも技術力が伝わります。

- 期待する表現
- 禁止したい表現
- 個人情報マスク
- プロンプトインジェクション検知
- 出力フォーマット

## 5. Docs as product

OSSのREADMEは営業資料でもあります。

最低限、以下を揃えます。

- 30秒Quickstart
- curl例
- manifest登録例
- architecture図
- security note
- eval strategy
- roadmap
- unofficial disclaimer

## 6. Next technical milestones

| Milestone | Why it matters |
|---|---|
| Async job adapter | 長時間処理・RAG対応 |
| TypeScript manifest types | フロントエンド連携と型安全 |
| Local runner UI | 源内Webなしで開発体験を改善 |
| RAG template | 行政FAQ・条例検索に展開 |
| Cloud blueprints | 実証・受託・自治体導入に使いやすい |
| Observability kit | ログ・メトリクス・監査証跡 |
