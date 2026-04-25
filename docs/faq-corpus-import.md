# FAQ corpus import

`citizen_faq_rag` はMarkdown形式のFAQコーパスを検索します。v0.5では、自治体FAQや手続き案内のCSV/JSONLを、RAGに読み込ませやすいMarkdownへ変換するCLIを追加しました。

## Supported input

CSVまたはJSONLで、以下の列を推奨します。

| field | meaning |
|---|---|
| `id` / `faq_id` | FAQ ID |
| `title` / `question` | 見出し |
| `category` | 分野 |
| `target` | 対象者 |
| `department` | 担当課 |
| `last_reviewed` | 最終確認日 |
| `source_url` | 公式URL |
| `body` / `answer` | 本文 |
| `required_items` | 必要なもの。`;` 区切り推奨 |
| `flow` | 手続きの流れ。`;` 区切り推奨 |
| `notes` | 注意事項 |

## Example

```bash
python scripts/import_faq_corpus.py \
  --input examples/faq.csv \
  --output apps/citizen_faq_rag/corpus/imported_faq.md \
  --title "My City FAQ"
```

生成後、Local Runnerの「追加の参照文書」に貼り付けるか、将来的にはファイル入力・外部コーパスローダーへ接続します。

## Production checklist

- 公式URL、担当課、最終確認日を必ず入れる
- 金額・期限・対象者は更新しやすい形で管理する
- FAQ本文に個人情報や内部情報を混ぜない
- evalケースを追加して、根拠なし断定が増えていないか確認する
