# GCP State Snapshot — Project 38 (V2)

**Generated:** 2024-12-15
**Status:** VERIFIED / FINAL_OK

---

## ⚠️ NO BUILD / NO DEPLOY YET ⚠️
This is PRE-BUILD phase. Infrastructure exists but no workloads are deployed.

---

## GCP Projects

### DEV
- **Project ID:** `project-38-ai`
- **Purpose:** Development environment
- **Status:** Active, secrets + IAM configured

### PROD
- **Project ID:** `project-38-ai-prod`
- **Purpose:** Production environment
- **Status:** Active, secrets + IAM configured

---

## Secrets (GCP Secret Manager)

### Status: SYNC_OK / FINAL_OK

**DEV (project-38-ai):**
All 7 secrets exist, each has **2 ENABLED versions**:
1. `anthropic-api-key`
2. `gemini-api-key`
3. `github-pat`
4. `n8n-encryption-key`
5. `openai-api-key`
6. `postgres-password`
7. `telegram-bot-token`

**PROD (project-38-ai-prod):**
Identical structure — same 7 secrets, each with **2 ENABLED versions**

**Important:**
- No dependency on local secret files (e.g., project_38_secret.txt)
- Everything stored in GCP Secret Manager
- **NEVER paste secret values in chat, files, Git, or logs**

---

## Service Accounts

### DEV (project-38-ai)
1. `github-actions-deployer@project-38-ai.iam.gserviceaccount.com`
2. `n8n-runtime@project-38-ai.iam.gserviceaccount.com`
3. `kernel-runtime@project-38-ai.iam.gserviceaccount.com`

### PROD (project-38-ai-prod)
1. `github-actions-deployer@project-38-ai-prod.iam.gserviceaccount.com`
2. `n8n-runtime@project-38-ai-prod.iam.gserviceaccount.com`
3. `kernel-runtime@project-38-ai-prod.iam.gserviceaccount.com`

---

## Secret Access Matrix (Least Privilege)

### github-actions-deployer
- **Access:** All 7 secrets
- **Purpose:** CI/CD pipeline, can inject secrets during deployment

### n8n-runtime
- **Access:**
  - `n8n-encryption-key`
  - `postgres-password`
  - `telegram-bot-token`
- **Purpose:** N8N workflow engine runtime

### kernel-runtime
- **Access:**
  - `openai-api-key`
  - `anthropic-api-key`
  - `gemini-api-key`
  - `github-pat`
- **Purpose:** Kernel/Agent runtime (LLM access + GitHub integration)

### kernel-runtime Additional Roles
- `roles/logging.logWriter` (write logs to Cloud Logging)
- `roles/compute.viewer` (read compute metadata)

---

## Verification Notes

- IAM bindings verified via `gcloud secrets get-iam-policy` (metadata only, no values)
- No secrets or IAM need to be recreated
- All configurations are DONE and VERIFIED

---

## Rules

1. Always specify `--project project-38-ai` or `--project project-38-ai-prod` in gcloud commands
2. Never create resources in any other GCP project
3. Do NOT recreate secrets/IAM that already exist
4. If verification needed: list names/metadata only, NEVER values
