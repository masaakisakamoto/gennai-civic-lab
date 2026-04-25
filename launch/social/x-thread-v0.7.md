# X thread draft for v0.7

## Post 1

源内互換の非公式OSS `gennai-civic-lab` を v0.7 まで進めました。

自治体・行政向けAIアプリを、ただ作るだけでなく、評価・安全性・RAG・Local Runner・運用レポート・Docker Blueprintまで含めて検証できるOSSです。

GitHub: <YOUR_GITHUB_URL>

## Post 2

v0.7の追加ポイント:

- persistent BM25 index
- corpus versioning
- Local Runner file upload
- release-readiness report
- X / Instagram launch kit

「AIアプリを作る」から「公開して育てられるOSS」に寄せました。

## Post 3

Citizen FAQ RAGは、回答に根拠・参照元・抜粋を出します。
根拠が弱い質問には、無理に答えず「担当課へ確認」と返します。

公共AIでは、答える力だけでなく、止まる力が重要だと思っています。

## Post 4

ローカルで試せます。

```bash
make install
make test
make eval
make red-team
make run-faq-rag
make run-local-runner
```

ブラウザでmanifestからフォームを生成して、源内互換APIへPOSTできます。

## Post 5

これは公式プロジェクトではありません。
ただ、源内の周辺エコシステムとして、自治体・公共領域で再利用できるAIアプリ開発基盤をOSSで育てる実験です。

改善アイデア・Issue・スター歓迎です。
