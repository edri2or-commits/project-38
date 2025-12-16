# Project Facts — Project 38 (V2)

**Last Updated:** 2025-12-16  
**System:** Project 38 (V2) — NEW system  
**Legacy:** AIOS (V1) — Reference only

---

## System Identity

- **NEW System:** Project 38 (V2)
- **Legacy System:** AIOS (V1)
- **Current Phase:** Phase 2 — Infrastructure & Deployment
- **Primary Google Account:** edri2or@gmail.com

---

## GCP Projects

### DEV Environment
- **Project ID:** `project-38-ai`
- **Purpose:** Development, testing, validation
- **Status:** Active
- **Region:** us-central1
- **Infrastructure:** Slice 1 COMPLETE (VM + Docker + IAM verified)

### PROD Environment
- **Project ID:** `project-38-ai-prod`
- **Purpose:** Production workloads
- **Status:** Active, secrets + IAM configured
- **Region:** (to be determined in Slice 4)

**Rules:**
- Every gcloud command MUST include `--project project-38-ai` or `--project project-38-ai-prod`
- Never create resources in any other GCP project
- DEV-first approach: build/test in DEV, then mirror to PROD after validation

---

## Repositories

### NEW Repository (Active)
**URL:** https://github.com/edri2or-commits/project-38  
**Purpose:** All Project 38 (V2) code, configs, and documentation

**Rules:**
- ✅ All commits, PRs, and changes go here
- ✅ Connected to CI/CD pipelines
- ✅ Targets GCP projects: `project-38-ai` (DEV) and `project-38-ai-prod` (PROD)

### LEGACY Repository (Reference Only)
**URL:** https://github.com/edri2or-commits/ai-os  
**Purpose:** Historical reference for AIOS (V1) system

**Rules:**
- ⛔ Read-only by default
- ⛔ No changes unless user provides keyword: `LEGACY_WRITE_OK`
- Reference for migration decisions only

---

## File System Paths

### NEW Workspace (Primary)
**Path:** `C:\Users\edri2\project_38`

**Rules:**
- ✅ WRITE ALLOWED — Active workspace
- ✅ All new files, configs, and docs go here
- Structure:
  ```
  C:\Users\edri2\project_38\
  ├── docs/
  │   ├── context/           ← Context snapshots (this file is here)
  │   ├── sessions/          ← Session logs
  │   └── drive_updates/
  │       └── pending/       ← Drive update requests
  ├── infra/                 ← Infrastructure configs (future)
  ├── workloads/            ← Service code (future)
  └── .github/              ← CI/CD workflows (future)
  ```

### LEGACY Workspace (Quarantine)
**Path:** `C:\Users\edri2\Desktop\AI\ai-os`

**Rules:**
- ⛔ READ-ONLY by default
- ⛔ No writes unless keyword: `LEGACY_WRITE_OK`
- Use for reference checks only

---

## Service Accounts

### DEV (project-38-ai)
| Service Account | Email | Purpose |
|-----------------|-------|---------||
| github-actions-deployer | github-actions-deployer@project-38-ai.iam.gserviceaccount.com | CI/CD deployments |
| n8n-runtime | n8n-runtime@project-38-ai.iam.gserviceaccount.com | N8N workflow engine |
| kernel-runtime | kernel-runtime@project-38-ai.iam.gserviceaccount.com | Kernel/Agent service |

### PROD (project-38-ai-prod)
| Service Account | Email | Purpose |
|-----------------|-------|---------||
| github-actions-deployer | github-actions-deployer@project-38-ai-prod.iam.gserviceaccount.com | CI/CD deployments |
| n8n-runtime | n8n-runtime@project-38-ai-prod.iam.gserviceaccount.com | N8N workflow engine |
| kernel-runtime | kernel-runtime@project-38-ai-prod.iam.gserviceaccount.com | Kernel/Agent service |

---

## Secret Access Matrix (Least Privilege)

### Summary Table

| Service Account | Secret Access | Project Roles |
|-----------------|---------------|---------------|
| **github-actions-deployer** | All 7 secrets | (deployment permissions) |
| **n8n-runtime** | n8n-encryption-key<br>postgres-password<br>telegram-bot-token | (compute permissions) |
| **kernel-runtime** | openai-api-key<br>anthropic-api-key<br>gemini-api-key<br>github-pat | roles/logging.logWriter<br>roles/compute.viewer |

### Detailed Secret Access

**github-actions-deployer:**
- ✅ anthropic-api-key
- ✅ gemini-api-key
- ✅ github-pat
- ✅ n8n-encryption-key
- ✅ openai-api-key
- ✅ postgres-password
- ✅ telegram-bot-token

**n8n-runtime:**
- ✅ n8n-encryption-key
- ✅ postgres-password
- ✅ telegram-bot-token
- ❌ No LLM API keys
- ❌ No GitHub access

**kernel-runtime:**
- ✅ openai-api-key
- ✅ anthropic-api-key
- ✅ gemini-api-key
- ✅ github-pat
- ❌ No N8N keys
- ❌ No database passwords

---

## Secrets Inventory

**Total:** 7 secrets per project  
**Projects:** 2 (DEV + PROD)  
**Versions per secret:** 2 ENABLED

### Secret List
1. `anthropic-api-key` — Claude API access
2. `gemini-api-key` — Gemini API access
3. `github-pat` — GitHub Personal Access Token
4. `n8n-encryption-key` — N8N data encryption
5. `openai-api-key` — OpenAI API access
6. `postgres-password` — Database credentials
7. `telegram-bot-token` — Telegram bot integration

**Status:** SYNC_OK / FINAL_OK / IAM_OK  
**Evidence:** See `secret_sync_history.md`

---

## Phase Status

**Current:** Phase 2 — Infrastructure & Deployment  
**Last Completed:** Slice 1 — VM Baseline (2025-12-15)  
**Next:** Slice 2A — N8N Deployment (awaiting execution approval)

**Completed:**
- ✅ GCP projects created
- ✅ Secrets configured (7×2 projects, 2 ENABLED versions each)
- ✅ IAM configured (3 SA per project, least privilege)
- ✅ Context documentation created
- ✅ Slice 1: DEV Infrastructure (VM: p38-dev-vm-01, Docker v29.1.3, Static IP: 136.111.39.139)

**Pending:**
- 📋 Slice 2A: N8N deployment (runbook ready, awaiting "Execute Slice 2A")
- ⏸️ Slice 2B/3: Kernel deployment (deferred - SA architecture decision needed)
- 📋 Slice 3: Testing & validation
- ⏸️ Slice 4: PROD mirror (after DEV validation)

**Deferred:**
- ⏸️ Advanced infrastructure (Cloud SQL, Cloud NAT, custom VPC) — only if scaling/managed DB required

---

## Important Distinctions

### Repository vs GCP Project IDs
⚠️ **Do NOT confuse:**

- **GitHub Repository:** `project-38` (in URL: github.com/edri2or-commits/project-38)
- **GCP DEV Project ID:** `project-38-ai`
- **GCP PROD Project ID:** `project-38-ai-prod`

The repository name is shorter; GCP project IDs include the `-ai` suffix.

### Workspaces
⚠️ **Do NOT confuse:**

- **NEW Workspace:** `C:\Users\edri2\project_38`
- **LEGACY Workspace:** `C:\Users\edri2\Desktop\AI\ai-os`

Always work in the NEW workspace unless explicitly told to access legacy.

---

## Contact & Access

- **Google Account:** edri2or@gmail.com
- **GitHub Account:** edri2or-commits
- **GCP Access:** Owner/Editor roles (as needed)
- **Drive SSOT:** DEPRECATED (repo is SSOT now)
