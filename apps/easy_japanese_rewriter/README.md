# easy_japanese_rewriter

行政文を市民に伝わる「やさしい日本語」へ変換する、源内互換AIアプリです。

## Design goals

- **意味を変えない**: 元文にない制度内容は追加しない
- **レビュー前提**: 法的・制度的判断は担当者確認として出す
- **安全性**: 個人情報らしき文字列のマスクとプロンプトインジェクション検知
- **デモしやすさ**: LLMキーなしでもルールベースfallbackで動く
- **拡張性**: OpenAI-compatible endpointを環境変数で差し替え可能

## Request

```json
{
  "inputs": {
    "text": "本制度の利用に際しては、所定の申請書類を提出してください。",
    "audience": "市民向け",
    "tone": "やさしい",
    "mode": "safe",
    "preserve_terms": "制度名、担当課名"
  }
}
```

## Response

```json
{
  "outputs": "# やさしい日本語への書き換え\n..."
}
```

## Run

```bash
uvicorn apps.easy_japanese_rewriter.app:app --reload --port 8000
```

## Demo curl

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H 'Content-Type: application/json' \
  -d '{"inputs":{"text":"本制度の利用に際しては、所定の申請書類を提出してください。","audience":"市民向け","tone":"やさしい","mode":"safe"}}'
```
