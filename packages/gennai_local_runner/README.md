# gennai-local-runner

ブラウザで源内互換AIアプリを試すためのローカル開発UIです。

## What it does

- `manifests/*.gennai.json` を読み込む
- 入力フォームを自動生成する
- ローカルで起動中のアプリ endpoint へPOSTする
- 同期レスポンス `{ "outputs": "Markdown" }` を表示する
- localhost以外へはデフォルトでPOSTしない

## Run

```bash
make run-local-runner
```

Open:

```text
http://127.0.0.1:8010/
```

別ターミナルで対象アプリも起動してください。

```bash
make run-easy-ja
# or
make run-faq-rag
```

## Security posture

v0.4では、誤送信を避けるため `http://127.0.0.1:*` と `http://localhost:*` だけを呼び出します。
実自治体データや機微情報を使う前に、組織のルール・接続先・ログ保存方針を確認してください。
