# Azure Deployment Blueprint

This is a reference architecture for organizations standardizing on Azure.

## Recommended shape

- **Azure Container Registry**: app images
- **Azure Container Apps**: Gennai-compatible API services
- **Application Gateway / internal ingress**: controlled access
- **Azure Monitor / Log Analytics**: metadata-only traces
- **Key Vault**: model credentials and service secrets
- **Blob Storage**: reviewed FAQ corpus snapshots
- **Managed Identity**: least-privilege access

## Guardrails

- Keep Local Runner internal-only.
- Avoid raw prompt/document logging by default.
- Use safe-mode PII masking in apps that handle public-facing text.
- Keep operational reports as deployment artifacts.

## Promotion checklist

Run these locally and in CI before promotion:

```bash
make test
make validate-manifests
make eval
make red-team
make eval-report
make demo-traces
make ops-report
```
