# citizen_faq_rag

自治体FAQ・手続き案内・制度情報を対象にした、源内互換のRAGアプリです。

## 特徴

- `{ "outputs": "Markdown text" }` で返す源内互換API
- 依存関係なしで動く deterministic lexical retriever
- Markdown FAQコーパスを自動分割
- 回答に根拠・参照元・抜粋を表示
- 根拠が弱い場合は断定せず、担当課確認へ誘導
- PIIマスキング
- プロンプトインジェクション検知
- YAML eval対応

## 起動

```bash
make run-faq-rag
```

または:

```bash
uvicorn apps.citizen_faq_rag.app:app --reload --port 8001
```

## curl

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

## 入力

| key | required | description |
|---|---:|---|
| `question` | yes | 市民からの質問 |
| `documents` | no | 追加のFAQ・手続き案内。Markdown推奨 |
| `files` | no | `.txt`, `.md`, `.csv`などの参照ファイル |
| `use_sample_corpus` | no | `yes`ならデモ用架空FAQを使用 |
| `answer_style` | no | `市民向け` / `職員向け` / `短く` |
| `mode` | no | `safe`ならPIIらしき文字列をマスク |
| `max_results` | no | 表示する根拠数 |

## 実データへ差し替えるとき

1. `apps/citizen_faq_rag/corpus/sample_faq.md` を参考に、自治体FAQをMarkdown化する。
2. `カテゴリ`, `担当課`, `最終確認日` を入れる。
3. evalに「答えられる質問」と「答えてはいけない質問」を追加する。
4. 本番投入前に、担当課レビュー・個人情報確認・最新性確認を行う。

## 注意

このアプリは開発・検証用の非公式OSSです。法的判断、制度適用判断、給付可否判定を自動化するものではありません。
