# Secret Sync History — Project 38 (V2)

**Last Updated:** 2024-12-15  
**Status:** SYNC_OK / FINAL_OK / IAM_OK

---

## ⚠️ CRITICAL: No Secret Values

This document contains **metadata only**.  
**NEVER** paste secret values in chat, files, Git, or logs.

---

## Current State: FINAL_OK

### Secrets in GCP Secret Manager

**Status:** SYNC_OK / FINAL_OK

Both DEV and PROD projects have identical secret structure:
- **7 secrets total**
- **Each secret has 2 ENABLED versions**
- **No local file dependencies** (e.g., project_38_secret.txt)

---

## Secret Inventory

### DEV: project-38-ai
| Secret Name | Versions | Status |
|-------------|----------|--------|
| anthropic-api-key | 2 ENABLED | ✅ |
| gemini-api-key | 2 ENABLED | ✅ |
| github-pat | 2 ENABLED | ✅ |
| n8n-encryption-key | 2 ENABLED | ✅ |
| openai-api-key | 2 ENABLED | ✅ |
| postgres-password | 2 ENABLED | ✅ |
| telegram-bot-token | 2 ENABLED | ✅ |

### PROD: project-38-ai-prod
| Secret Name | Versions | Status |
|-------------|----------|--------|
| anthropic-api-key | 2 ENABLED | ✅ |
| gemini-api-key | 2 ENABLED | ✅ |
| github-pat | 2 ENABLED | ✅ |
| n8n-encryption-key | 2 ENABLED | ✅ |
| openai-api-key | 2 ENABLED | ✅ |
| postgres-password | 2 ENABLED | ✅ |
| telegram-bot-token | 2 ENABLED | ✅ |

---

## IAM Configuration: IAM_OK

### Service Accounts per Project

**DEV (project-38-ai):**
1. `github-actions-deployer@project-38-ai.iam.gserviceaccount.com`
2. `n8n-runtime@project-38-ai.iam.gserviceaccount.com`
3. `kernel-runtime@project-38-ai.iam.gserviceaccount.com`

**PROD (project-38-ai-prod):**
1. `github-actions-deployer@project-38-ai-prod.iam.gserviceaccount.com`
2. `n8n-runtime@project-38-ai-prod.iam.gserviceaccount.com`
3. `kernel-runtime@project-38-ai-prod.iam.gserviceaccount.com`

---

## Secret Access Permissions (Least Privilege)

### github-actions-deployer
**Access:** All 7 secrets  
**Purpose:** CI/CD pipeline deployments

| Secret | Access |
|--------|--------|
| anthropic-api-key | ✅ Read |
| gemini-api-key | ✅ Read |
| github-pat | ✅ Read |
| n8n-encryption-key | ✅ Read |
| openai-api-key | ✅ Read |
| postgres-password | ✅ Read |
| telegram-bot-token | ✅ Read |

### n8n-runtime
**Access:** 3 secrets (workflow engine needs)  
**Purpose:** N8N runtime operations

| Secret | Access |
|--------|--------|
| n8n-encryption-key | ✅ Read |
| postgres-password | ✅ Read |
| telegram-bot-token | ✅ Read |
| anthropic-api-key | ❌ No Access |
| gemini-api-key | ❌ No Access |
| github-pat | ❌ No Access |
| openai-api-key | ❌ No Access |

### kernel-runtime
**Access:** 4 secrets (LLM + GitHub integration)  
**Purpose:** Kernel/Agent runtime

| Secret | Access |
|--------|--------|
| openai-api-key | ✅ Read |
| anthropic-api-key | ✅ Read |
| gemini-api-key | ✅ Read |
| github-pat | ✅ Read |
| n8n-encryption-key | ❌ No Access |
| postgres-password | ❌ No Access |
| telegram-bot-token | ❌ No Access |

**Additional Roles for kernel-runtime:**
- `roles/logging.logWriter` — Write logs to Cloud Logging
- `roles/compute.viewer` — Read compute resource metadata

---

## Verification Evidence

✅ **Secrets verified via:**
```bash
gcloud secrets list --project=project-38-ai
gcloud secrets list --project=project-38-ai-prod
```

✅ **IAM bindings verified via:**
```bash
gcloud secrets get-iam-policy <secret-name> --project=<project-id>
```

✅ **Service accounts verified via:**
```bash
gcloud iam service-accounts list --project=<project-id>
```

**Note:** All verification commands used metadata only (no secret values accessed).

---

## Anti-Chaos Rules

### Do NOT:
1. ❌ Recreate secrets (they already exist with SYNC_OK / FINAL_OK status)
2. ❌ Recreate service accounts (IAM_OK status confirmed)
3. ❌ Paste secret values anywhere (chat, files, Git, logs)
4. ❌ Access secret values without explicit instruction for validation
5. ❌ Modify IAM bindings without documented justification

### If Verification Needed:
✅ List secret names: `gcloud secrets list --project=...`  
✅ List SA names: `gcloud iam service-accounts list --project=...`  
✅ Check IAM policy: `gcloud secrets get-iam-policy ... --project=...`  
❌ DO NOT: `gcloud secrets versions access latest ...` (unless explicitly instructed)

---

## History Log

| Date | Action | Status | Notes |
|------|--------|--------|-------|
| 2024-12-15 | Initial sync verification | SYNC_OK | 7 secrets × 2 projects verified |
| 2024-12-15 | IAM configuration verified | IAM_OK | 3 SA per project + least privilege |
| 2024-12-15 | Final approval | FINAL_OK | No changes needed, ready for use |
| 2025-12-17 | VM deployment audit | 🚨 DRIFT | Found: Containers using placeholder `\` instead of GCP secrets |
| 2025-12-17 | Secret injection investigation | PENDING | load-secrets.sh exists but not executed; awaiting re-deployment |

---

## 🚨 Current Issue: Placeholder Secrets on VM (2025-12-17)

### Discovery
**Session:** [2025-12-17 Drift Verification](../sessions/2025-12-17_drift_verification.md)

**Finding:** VM containers (p38-postgres, p38-n8n) running with backslash literals instead of real secrets:

| Secret in GCP | Container Value | Expected Value Source |
|---------------|----------------|----------------------|
| postgres-password | `\` (2 bytes) | GCP Secret Manager |
| n8n-encryption-key | `\` (2 bytes) | GCP Secret Manager |
| telegram-bot-token | `\` (2 bytes) | GCP Secret Manager |

**Evidence:**
```bash
# All secrets are 2-byte backslash literals
docker exec p38-postgres printenv POSTGRES_PASSWORD | wc -c  # 2
docker exec p38-n8n printenv N8N_ENCRYPTION_KEY | wc -c      # 2
docker exec p38-n8n printenv N8N_TELEGRAM_BOT_TOKEN | wc -c  # 2

# First byte is 0x5c (backslash)
docker exec p38-postgres printenv POSTGRES_PASSWORD | head -c 1 | od -An -tx1
# Output: 5c
```

**Root Cause:**
- VM deployment: `docker compose up -d` run directly (bypassed `./load-secrets.sh`)
- File `/home/edri2/docker-compose.yml` contains hardcoded placeholder values:
  ```yaml
  POSTGRES_PASSWORD: \
  N8N_ENCRYPTION_KEY: \
  N8N_TELEGRAM_BOT_TOKEN: \
  ```
- Script `/home/edri2/load-secrets.sh` exists but was NOT executed

**Impact:**
- ⚠️ **N8N encryption weak:** Encryption key is `\` (not cryptographically secure)
- ⚠️ **Telegram bot inactive:** Token `\` is invalid for Telegram API
- ✅ **Postgres functional:** Password `\` works (SCRAM-SHA-256 authenticated)

**Safety Validation:**
- ✅ **0 credentials** in database → Safe to re-deploy without data loss
- ✅ **6 simple workflows** (webhook POCs, no credential nodes)
- ✅ **No encryption errors** in logs

**Resolution Plan:**
1. Execute `/home/edri2/load-secrets.sh` on VM
2. Verify secret lengths: `docker exec p38-postgres printenv POSTGRES_PASSWORD | wc -c` (should be >20)
3. Restart containers with real secrets
4. Update deployment runbook to enforce `./load-secrets.sh` step

**Status:** Awaiting user approval for re-deployment

---

## Next Steps

- **NO ACTION REQUIRED** — Secrets and IAM are DONE
- When Slice 1 (Infrastructure) begins: validate secret access during workload deployment
- Use impersonation for testing: `--impersonate-service-account=...`
