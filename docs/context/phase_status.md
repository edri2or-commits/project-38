# Phase Status — Project 38 (V2)

**Last Updated:** 2024-12-15

---

## Current Phase: PRE-BUILD

**Status:** Planning + Bootstrap (no workload deployments yet)

**Mode:** Documentation and context ingestion only

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
- ✅ gcp_state_snapshot.md created
- ✅ repos_and_paths.md created
- ✅ phase_status.md created (this file)

---

## 🔄 NEXT (When Instructed)

### Slice 1: DEV Environment Setup
**Target:** `project-38-ai` only

**Tasks:**
1. **Validate secret access**
   - Use metadata checks only (do NOT create secrets)
   - Verify service accounts can read assigned secrets
   - Test: `gcloud secrets versions access latest --secret=<name> --impersonate-service-account=<SA>`

2. **Network setup**
   - Create VPC if needed
   - Configure Cloud NAT (for private VMs to access internet)
   - Set up firewall rules

3. **Compute infrastructure**
   - Deploy VM(s) for kernel/n8n (if using GCE)
   - OR configure Cloud Run services
   - Assign service accounts to workloads

4. **Storage setup**
   - Cloud SQL (PostgreSQL) for n8n state
   - OR managed database alternative

5. **Deploy workloads**
   - N8N engine
   - Kernel/Agent service
   - Configure inter-service communication

6. **Testing & validation**
   - Smoke tests
   - Secret injection verification
   - Logging verification

**Important:**
- Start with DEV only
- No PROD deployments until DEV is validated
- All changes tracked in Git

---

## ⛔ DO NOT DO (Anti-Chaos Rules)

### Never
1. ❌ Paste or request secret values in chat, files, Git, or logs
2. ❌ Recreate secrets/IAM that already exist (they are DONE)
3. ❌ Deploy to PROD before DEV validation
4. ❌ Create resources in any GCP project other than `project-38-ai` or `project-38-ai-prod`
5. ❌ Write to legacy workspace (`ai-os`) without `LEGACY_WRITE_OK` keyword
6. ❌ Auto-sync to Drive (create update requests instead)
7. ❌ Run gcloud commands without `--project` flag
8. ❌ Assume facts not in the Facts Block

### Verification Only
- If you need to verify secrets/IAM: list names/metadata ONLY
- Use: `gcloud secrets list --project=...`
- Use: `gcloud iam service-accounts list --project=...`
- DO NOT use: `gcloud secrets versions access ...` (unless explicitly instructed for validation)

---

## Phase Progression

```
Current → PRE-BUILD (✅ we are here)
Next    → Slice 1: DEV Infrastructure (when user instructs)
Then    → Slice 2: DEV Workload Deploy
Then    → Slice 3: DEV Testing & Validation
Then    → Slice 4: PROD Mirror (after DEV approval)
```

---

## Decision Points

Before proceeding to next phase, user must:
- ✅ Review and approve context documentation
- ✅ Explicitly instruct to start Slice 1
- ✅ Confirm no additional secrets/IAM changes needed

**Current status:** Waiting for user instruction to proceed.
