# AWS Deployment Blueprint

This is a reference architecture, not a one-click production template.

## Recommended shape

- **ECR**: container images for each Gennai-compatible app
- **ECS Fargate**: `easy_japanese_rewriter`, `citizen_faq_rag`, and optional Local Runner for internal demos
- **Application Load Balancer**: private/internal ALB where possible
- **CloudWatch Logs**: metadata-only logs and traces
- **Secrets Manager**: API keys and external model credentials if enabled
- **S3**: curated FAQ corpus snapshots, versioned and reviewed
- **IAM**: least-privilege task roles

## Guardrails

- Do not expose Local Runner publicly.
- Prefer private subnets and internal service-to-service calls.
- Store raw citizen input only if your data policy explicitly allows it.
- Send only metadata-first traces: app id, duration, status, retrieval backend, hit count.
- Keep corpus source, updated date, and review owner in metadata.

## Promotion checklist

1. `make test`
2. `make validate-manifests`
3. `make eval`
4. `make red-team`
5. `make eval-report`
6. `make ops-report`
7. Security review of corpus and logging policy
