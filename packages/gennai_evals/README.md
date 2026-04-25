# gennai-evals

YAML-based smoke/eval runner for Gennai-compatible AI apps.

```yaml
app: easy_japanese_rewriter
cases:
  - name: simple rewrite
    input:
      inputs:
        text: 本制度の利用に際しては、所定の申請書類を提出してください。
    expect_contains:
      - この制度
      - 出してください
    expect_not_contains:
      - 利用に際して
```

```bash
python packages/gennai_evals/src/gennai_evals/runner.py evals/easy_japanese.yaml
```


## Reports

```bash
python packages/gennai_evals/src/gennai_evals/runner.py \
  --markdown-report reports/eval-report.md \
  --json-report reports/eval-report.json \
  evals/easy_japanese.yaml evals/citizen_faq.yaml
```
