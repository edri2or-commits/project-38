# GitHub Webhook Receiver

Cloud Run service for receiving and validating GitHub webhook deliveries.

## Features

- ✅ **Signature Verification:** HMAC-SHA256 validation of all incoming webhooks
- ✅ **Secret Manager Integration:** Secure secret injection from GCP Secret Manager
- ✅ **Redacted Logging:** Only delivery IDs logged, no headers/body/secrets
- ✅ **Dedicated Service Account:** Least privilege access

## Deployment

```bash
gcloud run deploy github-webhook-receiver \
  --source=. \
  --region=us-central1 \
  --project=project-38-ai \
  --set-secrets=WEBHOOK_SECRET=github-webhook-secret:latest \
  --service-account=github-webhook-receiver-sa@project-38-ai.iam.gserviceaccount.com
```

## Documentation

- **[Signature Verification](SIGNATURE_VERIFICATION.md)** - Security implementation & validation gates

## Architecture

```
GitHub App
    |
    | POST /webhook
    | X-Hub-Signature-256: sha256=<hmac>
    |
    v
Cloud Run Service
    |
    |-- Validate Signature (HMAC-SHA256)
    |   |
    |   |-- ❌ Invalid → 401 (log: "rejected: invalid signature")
    |   |-- ✅ Valid → 200 (log: "received (delivery_id: <id>)")
    |
    |-- WEBHOOK_SECRET (from Secret Manager)
```

## Testing

See [SIGNATURE_VERIFICATION.md](SIGNATURE_VERIFICATION.md) for validation gates.

## Service URLs

- **Production:** https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app
- **GitHub App:** https://github.com/settings/apps/project-38-scribe
