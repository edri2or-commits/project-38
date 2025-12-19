# GitHub Webhook Signature Verification

**Date:** 2025-12-19  
**Status:** ✅ PRODUCTION  
**Service:** github-webhook-receiver (Cloud Run)

---

## Overview

The webhook receiver validates all incoming GitHub webhook deliveries using HMAC-SHA256 signature verification as per [GitHub's webhook security guidelines](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries).

---

## How It Works

### 1. GitHub Sends Signature
Every webhook delivery includes an `X-Hub-Signature-256` header:
```
X-Hub-Signature-256: sha256=<hexdigest>
```

### 2. Cloud Run Validates
The receiver:
1. Reads `WEBHOOK_SECRET` from Secret Manager
2. Computes HMAC-SHA256 over the raw request body
3. Compares using timing-safe comparison (`hmac.compare_digest`)
4. Returns **401** if signature is missing or invalid
5. Returns **200** if valid

### 3. Logging (Redacted)
- ✅ Valid: `POST /webhook received (delivery_id: <id>)`
- ❌ Invalid: `POST /webhook rejected: invalid signature (delivery_id: <id>)`
- **No headers/body/secrets** are logged

---

## Validation Gates

Before accepting any deployment, run these tests:

### Gate 1: No Signature → 401
```bash
curl -X POST https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Expected: HTTP 401
```

### Gate 2: Invalid Signature → 401
```bash
curl -X POST https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=invalid_signature_12345" \
  -d '{"test":"data"}'

# Expected: HTTP 401
# Expected log: "POST /webhook rejected: invalid signature"
```

### Gate 3: Valid GitHub Delivery → 200
Trigger a ping from GitHub App settings:
- https://github.com/settings/apps/project-38-scribe
- Advanced → Recent Deliveries → Redeliver

```
# Expected: HTTP 200
# Expected log: "POST /webhook received (delivery_id: <id>)"
```

---

## Secret Management

### Secret Creation
```bash
# 1. Create secret in Secret Manager
gcloud secrets create github-webhook-secret \
  --project=project-38-ai \
  --data-file=/path/to/secret.txt

# 2. Grant access to service account
gcloud secrets add-iam-policy-binding github-webhook-secret \
  --project=project-38-ai \
  --member="serviceAccount:github-webhook-receiver-sa@project-38-ai.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Secret Injection (Cloud Run)
```bash
gcloud run deploy github-webhook-receiver \
  --source=. \
  --region=us-central1 \
  --project=project-38-ai \
  --set-secrets=WEBHOOK_SECRET=github-webhook-secret:latest \
  --service-account=github-webhook-receiver-sa@project-38-ai.iam.gserviceaccount.com
```

The secret is mounted as an environment variable `WEBHOOK_SECRET` at runtime.

---

## GitHub App Configuration

### Webhook Settings
**Location:** https://github.com/settings/apps/project-38-scribe

```yaml
Webhook URL: https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook
Webhook secret: <value from Secret Manager>
Active: ✅ Yes
```

**Important:** Both GitHub and Cloud Run must use the **same secret value**.

---

## Security Properties

✅ **HMAC-SHA256:** Industry-standard signature algorithm  
✅ **Timing-safe comparison:** Mitigates timing attacks (`hmac.compare_digest`)  
✅ **Secret from Secret Manager:** Not hardcoded or in environment variables  
✅ **Dedicated service account:** Least privilege (not default compute SA)  
✅ **Redacted logging:** No headers, body, or secret values in logs  

---

## References

- [GitHub: Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [GitHub: Handling webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries)
- [GitHub: Best practices for webhooks](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
- [Cloud Run: Secrets injection](https://docs.cloud.google.com/run/docs/configuring/services/secrets)

---

## Future Enhancements

- [ ] **Idempotency:** Track `X-GitHub-Delivery` header to prevent duplicate processing
- [ ] **Replay protection:** Reject deliveries older than N minutes
- [ ] **Rate limiting:** Protect against abuse

---

*Last validated: 2025-12-19*
