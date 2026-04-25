# gennai-cli

新しい源内互換アプリの雛形を作るCLIです。

## Create app

```bash
python packages/gennai_cli/src/gennai_cli/create_app.py document-risk-checker
```

生成されるもの:

```text
apps/document_risk_checker/
manifests/document_risk_checker.gennai.json
evals/document_risk_checker.yaml
tests/test_document_risk_checker.py
```

## Installed script

```bash
gennai-create-app document-risk-checker
```
