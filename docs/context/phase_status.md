# Phase Status — Project 38 (V2)

**Last Updated:** 2025-12-15

---

## Current Phase: Phase 2 — Infrastructure & Deployment

**Status:** Slice 1 ✅ COMPLETE, Slice 2A 📋 PLANNED (awaiting execution approval)

**Mode:** Incremental deployment with approval gates

---

## ✅ DONE (Verified & Final)

### 1. GCP Projects Created
- DEV: `project-38-ai` ✅
- PROD: `project-38-ai-prod` ✅

### 2. Secrets (GCP Secret Manager)
- **Status:** SYNC_OK / FINAL_OK
- DEV: 7 secrets, each with 2 ENABLED versions ✅
- PROD: 7 secrets, each with 2 ENABLED versions ✅
- List:
  1. anthropic-api-key
  2. gemini-api-key
  3. github-pat
  4. n8n-encryption-key
  5. openai-api-key
  6. postgres-password
  7. telegram-bot-token

### 3. Service Accounts (IAM)
- **Status:** IAM_OK
- DEV: 3 service accounts created ✅
  - github-actions-deployer
  - n8n-runtime
  - kernel-runtime
- PROD: 3 service accounts created ✅
  - github-actions-deployer
  - n8n-runtime
  - kernel-runtime

### 4. Secret Access Matrix (Least Privilege)
- ✅ github-actions-deployer → all 7 secrets
- ✅ n8n-runtime → 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token)
- ✅ kernel-runtime → 4 secrets (openai-api-key, anthropic-api-key, gemini-api-key, github-pat)
- ✅ kernel-runtime project roles: logging.logWriter + compute.viewer

### 5. Workspace & Repository
- ✅ NEW workspace: C:\Users\edri2\project_38
- ✅ NEW repo: github.com/edri2or-commits/project-38
- ✅ LEGACY quarantine: C:\Users\edri2\Desktop\AI\ai-os (READ-ONLY)

### 6. Context Documentation
- ✅ Strategic Narrative created (PROJECT_NARRATIVE.md)
- ✅ Source of Truth files established (docs/context/)
- ✅ Traceability Matrix created
- ✅ Evidence protocol documented

### 7. Infrastructure (Slice 1 — VM Baseline)
- **Status:** ✅ COMPLETE (2025-12-15, execution duration: 4min 30sec)
- **VM:** p38-dev-vm-01 (e2-medium, us-central1-a)
- **Static IP:** p38-dev-ip-01 (136.111.39.139)
- **Firewall:** SSH (22), HTTP (80), HTTPS (443)
- **Docker:** v29.1.3 + Docker Compose v5.0.0 installed
- **Service Account:** n8n-runtime attached and secret access verified
- **Evidence:** [Execution Log](../phase-2/slice-01_execution_log.md)

---

## 📋 NEXT (Awaiting Explicit Approval)

### Slice 2A: N8N + Postgres Deployment
**Target:** `project-38-ai` (DEV) only

**Scope:**
- Deploy n8n workflow engine (n8nio/n8n:latest)
- Deploy PostgreSQL database (postgres:16-alpine)
- Access via SSH port-forward (localhost:5678 → VM:5678)
- Use n8n-runtime SA (3 secrets only: n8n-encryption-key, postgres-password, telegram-bot-token)

**Documentation:**
- ✅ [Runbook](../phase-2/slice-02a_runbook.md) — 7-step execution plan
- ✅ [Evidence Pack](../phase-2/slice-02a_evidence_pack.md) — Capture requirements
- ✅ [Rollback Plan](../phase-2/slice-02a_rollback_plan.md) — Cleanup procedures

**Approval Required:** User must say **"Execute Slice 2A"**

---

## ⏸️ DEFERRED

### Slice 2B/3: Kernel Service Deployment
**Blocker:** Service account architecture decision

**Options:**
1. Separate VM with kernel-runtime SA (recommended)
2. Multi-SA on same VM (if GCP supports)
3. Credential file approach (less preferred)

**Dependencies:** Slice 2A completion + architecture decision

---

### Advanced Infrastructure (Phase 3)
**Components:**
- Cloud SQL (managed PostgreSQL)
- Custom VPC with Cloud NAT
- litellm migration to Cloud Run
- Load balancing for horizontal scaling

**Trigger:** Only if VM baseline hits scaling limits or ops burden

**Dependencies:** 3+ months stable VM operations + cost-benefit analysis

---

## ⛔ DO NOT DO (Anti-Chaos Rules)

### Never
1. ❌ Paste or request secret values in chat, files, Git, or logs
2. ❌ Recreate secrets/IAM that already exist (they are DONE)
3. ❌ Deploy to PROD before DEV validation
4. ❌ Create resources in any GCP project other than `project-38-ai` or `project-38-ai-prod`
5. ❌ Write to legacy workspace (`ai-os`) without `LEGACY_WRITE_OK` keyword
6. ❌ Auto-sync to Drive (Drive is deprecated, repo is SSOT)
7. ❌ Run gcloud commands without `--project` flag
8. ❌ Assume facts not in documentation

### Verification Only
- If you need to verify secrets/IAM: list names/metadata ONLY
- Use: `gcloud secrets list --project=...`
- Use: `gcloud iam service-accounts list --project=...`
- DO NOT use: `gcloud secrets versions access ...` (unless explicitly instructed for validation)

---

## Phase Progression

```
Phase 1 → Analysis & Planning ✅ COMPLETE
Phase 2 → Infrastructure & Deployment 🔄 IN PROGRESS
  ├─ Slice 1: VM Baseline ✅ COMPLETE (2025-12-15)
  ├─ Slice 2A: N8N Deployment 📋 PLANNED (awaiting approval)
  ├─ Slice 2B/3: Kernel Deployment ⏸️ DEFERRED (architecture TBD)
  └─ Slice 3: Testing & Validation 📋 NEXT (after Slice 2A)
Phase 3 → Advanced Infrastructure ⏸️ OPTIONAL (only if needed)
Phase 4 → PROD Mirror ⏸️ DEFERRED (after DEV validation)
```

---

## Decision Points

Before proceeding to Slice 2A:
- ✅ Slice 1 complete and verified
- ✅ Documentation reviewed (runbook, evidence pack, rollback plan)
- ❓ User approval required: **"Execute Slice 2A"**

Before proceeding to Slice 2B/3:
- ❌ Slice 2A must be complete
- ❌ Service account architecture decision required
- ❌ User approval required

**Current status:** Ready for Slice 2A execution (awaiting approval)
