# Project 38 V2 — Strategic Narrative

**Last Updated:** 2025-12-21  
**Status:** Phase 2 — Infrastructure & IssueOps Active  
**Control Room:** [Issue #24](https://github.com/edri2or-commits/project-38/issues/24) — Chat & state authority  
**Quick Links:** [SYSTEM_MAP.md](docs/_system/SYSTEM_MAP.md) · [Architecture Decisions](#architecture-decisions) · [Current State](#where-we-are-now) · [Operating Model](#operating-model)

---

## 🎯 Why We're Here

### The Legacy System (AIOS V1)

For months, AIOS V1 served as a personal AI automation platform — a constellation of 6 Docker containers orchestrating workflows between Telegram, Claude, OpenAI, and dozens of integrations. **It worked.** Users could trigger workflows via Telegram, n8n would orchestrate the logic, LLM agents would process requests, and responses would flow back seamlessly.

**But under the surface, cracks were forming.**

### The Pain Points That Forced a Rebuild

**1. GitOps Blocker #1: Credential Hell**
```
Reality: Manual credential import into n8n UI
Problem: Secrets couldn't be version-controlled
Impact: Every deployment required clicking through the UI
        Fresh environment = start from scratch
        No automation = no CI/CD
```

**Why it hurt:** You can't GitOps a system that requires manual UI clicks to function.

**2. GitOps Blocker #2: Workflow Activation Roulette**
```
Reality: n8n CLI couldn't reliably activate workflows
Problem: Webhooks wouldn't register via API
Impact: Deploy → SSH → activate manually → hope it sticks
        Production workflows randomly deactivated
        No confidence in deployment process
```

**Why it hurt:** Production reliability dependent on manual intervention defeats the purpose of automation.

**3. GitOps Blocker #3: Environment Variable Drift**
```
Reality: .env files in multiple locations
Problem: VM has one truth, container has another, Git has a third
Impact: Silent failures when env vars don't match
        Debugging = guessing which env var source is wrong
        "Works on my machine" = production nightmare
```

**Why it hurt:** Multiple sources of truth = no source of truth.

**4. Silent Component Failures**
```
Reality: litellm shows UNHEALTHY, system keeps running
Problem: No dependency health checks at startup
Impact: Workflows fail mysteriously hours later
        Users report issues before monitoring does
        Root cause = component failed 3 days ago
```

**Why it hurt:** System appears healthy while slowly dying inside.

**5. Missing Env Vars = Silent Death**
```
Reality: Personal agent workflow listed as "active" but non-functional
Problem: Missing env vars treated as optional, not fatal
Impact: Workflow activates successfully, then fails on first run
        No validation = false confidence
        Discovery = user complaint, not deployment check
```

**Why it hurt:** Deployment success doesn't mean system success.

### The Breaking Point

**The question wasn't "Should we improve V1?" — it was "Can V1 even be GitOps-ready?"**

After deep analysis, the answer was **no**. The fundamental design — manual credential injection, unreliable activation APIs, fragmented env var management — couldn't be patched. It needed to be **redesigned from first principles.**

---

## 🚀 What We're Building

### Vision: Production-Grade AI Automation Platform

**Project 38 V2** is a complete rebuild with three non-negotiable goals:

**1. GitOps-Native from Day 1**
- Every credential injected via GCP Secret Manager
- Every workflow activated via Infrastructure-as-Code
- Every deployment 100% reproducible
- Zero manual UI clicks required

**2. Infrastructure-as-Evidence**
- Every resource change documented with SHA256-verified evidence
- Every deployment decision traceable to documented rationale
- Every failure mode anticipated with documented rollback plans
- Production confidence through comprehensive evidence, not hope

**3. Least-Privilege Security Model**
- 3 service accounts, each with minimal required permissions
- Secrets accessible only to services that need them
- n8n can't access LLM API keys (kernel's job)
- Kernel can't access database passwords (n8n's job)

### What Changed from V1 to V2

| Aspect | AIOS V1 (Legacy) | Project 38 V2 (New) |
|--------|------------------|---------------------|
| **Credentials** | Manual UI import | GCP Secret Manager → env vars |
| **Activation** | CLI (unreliable) + manual | API + health validation gates |
| **Env Vars** | Multiple .env files, drift | Single source (.env from Secret Manager) |
| **Health Checks** | Per-service only | Pre-flight + dependency validation |
| **Evidence** | Tribal knowledge | SHA256-verified artifact store |
| **Rollback** | Manual recovery | Automated scripts + health gates |
| **Security** | Single service account | 3 SAs with least privilege |

---

## 🏗️ How We're Building It

### Architecture Decisions

#### Decision 1: VM-First Strategy (Gate A)

**The Choice:** Start with Compute Engine VM, not Cloud Run.

**Why VM Over Cloud Run?**

| Factor | Why It Matters | Rationale |
|--------|----------------|-----------|
| **Webhook Reliability** | Telegram webhooks require <3s response time | Cold starts (1-5s) fail SLA; VM = 0ms startup |
| **Debugging Access** | Production issues need immediate investigation | SSH + docker logs vs console-only logs |
| **Proven Stability** | V1 ran successfully on VMs for 6+ months | Reduce risk by keeping what worked |
| **Stateful Workflows** | n8n + Postgres + Redis need shared local network | VM = simple networking, Cloud Run = Cloud SQL + VPC config |
| **Rollback Speed** | Failed deploy needs instant recovery | VM: swap compose file (5s), Cloud Run: redeploy image (30-60s) |

**Migration Path:** Once baseline proves stable, litellm (stateless LLM proxy) moves to Cloud Run for auto-scaling. n8n stays on VM for webhook reliability.

**Evidence:** See [gateA_vm_first.md](docs/phase-1/gateA_vm_first.md) for full decision matrix.

---

#### Decision 2: Three Service Accounts (Least Privilege)

**The Problem:** V1 used one service account for everything — violation of least privilege.

**The Solution:** Split responsibilities across 3 specialized service accounts.

**Service Account Matrix:**

| Service Account | Purpose | Secret Access | Project Roles |
|-----------------|---------|---------------|---------------|
| **github-actions-deployer** | CI/CD pipelines | All 7 secrets | Deployment permissions |
| **n8n-runtime** | Workflow engine | 3 secrets:<br>• n8n-encryption-key<br>• postgres-password<br>• telegram-bot-token | (compute only) |
| **kernel-runtime** | AI agent service | 4 secrets:<br>• openai-api-key<br>• anthropic-api-key<br>• gemini-api-key<br>• github-pat | roles/logging.logWriter<br>roles/compute.viewer |

**Why This Matters:**
- n8n compromise ≠ LLM API key exposure
- Kernel compromise ≠ database password exposure  
- GitHub Actions compromise = contained to deployment scope
- Blast radius minimized for each component

**Evidence:** IAM policies verified in [Slice 1 Execution Log](docs/phase-2/slice-01_execution_log.md#step-5-validate-service-account-secret-access).

---

#### Decision 3: Repo-Based Single Source of Truth (SSOT)

**The Problem:** V1 relied on Google Drive for documentation, leading to:
- Sync lag between Drive and repo
- Version control conflicts
- Manual Drive updates after every session
- No audit trail for doc changes

**The Solution:** Repository = SSOT, Drive deprecated.

**What Lives Where:**

```
📦 Repository (Git-tracked)
├── docs/context/            ← Source of truth (facts, rules, status)
├── docs/phase-N/            ← Decision records, runbooks, evidence logs
├── docs/evidence/           
│   └── manifest.md          ← SHA256 hashes of external artifacts
└── PROJECT_NARRATIVE.md     ← This document (entry point)

📁 External Evidence Store (Not committed)
└── C:\Users\edri2\project_38__evidence_store\
    ├── phase-2/slice-01/    ← RAW command outputs, logs, screenshots
    └── phase-2/slice-02a/   ← (future) N8N deployment evidence
```

**Benefits:**
- ✅ Git history = audit trail of all decisions
- ✅ No Drive sync lag
- ✅ SHA256 hashes ensure evidence integrity
- ✅ New sessions start from repo, not memory

**Evidence:** See [ssot_and_evidence_protocol.md](docs/context/ssot_and_evidence_protocol.md).

---

#### Decision 4: Slice-Based Deployment with Approval Gates

**The Problem:** V1 deployed monolithically — all or nothing, high risk.

**The Solution:** Break deployment into small, verifiable slices with explicit approval required.

**Slice Progression:**

```
Phase 1: Analysis & Planning ✅ DONE
  └─ Lessons from V1
  └─ Architecture decisions
  └─ Service account design

Phase 2: Infrastructure & Deployment
  ├─ Slice 1: VM Baseline ✅ DONE (2025-12-15, 4min 30sec)
  │   └─ VM + Docker + IAM verified
  ├─ Slice 2A: N8N Deployment 📋 PLANNED
  │   └─ n8n + Postgres (3 secrets, least privilege)
  ├─ Slice 2B/3: Kernel Deployment ⏸️ DEFERRED
  │   └─ Kernel service (4 secrets, separate SA architecture TBD)
  └─ Slice 3: Testing & Validation 📋 NEXT
      └─ End-to-end smoke tests

Phase 3: Advanced Infrastructure (Optional)
  └─ ⏸️ Cloud SQL, VPC, Cloud Run migration (only if scaling needed)
```

**Why Slices Work:**
- Each slice has clear entry/exit criteria
- Stop conditions prevent runaway failures
- Rollback plans documented before execution
- Evidence captured at every step
- Explicit approval required: `"Execute Slice 2A"` ← exact phrase

**Evidence:** See [traceability_matrix.md](docs/traceability_matrix.md) for component status.

---

### Patterns Extracted from V1

#### ✅ Patterns to KEEP

| Pattern | Why It Worked | V2 Implementation |
|---------|---------------|-------------------|
| **Container-based isolation** | Clear service boundaries, independent restarts | Keeping Docker Compose approach |
| **Health monitoring per service** | Early failure detection (litellm UNHEALTHY flagged) | Enhanced with pre-flight dependency checks |
| **Reverse proxy (Caddy)** | Single HTTPS endpoint, automatic cert renewal | Keeping Caddy for TLS termination |
| **External observability (Langfuse)** | Reduced ops burden vs self-hosted | Keeping cloud-based tracing |
| **VM-based runtime** | SSH access for debugging, proven stability | VM-first strategy (Gate A) |

#### ❌ Anti-Patterns to AVOID

| Anti-Pattern | Root Cause | V2 Prevention |
|--------------|------------|---------------|
| **Credential injection hell** | No env var management | GCP Secret Manager + scripted injection |
| **Workflow activation roulette** | Unreliable n8n CLI | API activation + health validation |
| **Env var drift** | Multiple .env sources | Single source: Secret Manager → `.env` file |
| **Silent component failures** | No startup dependency checks | Pre-flight validation: n8n waits for postgres/redis UP |
| **Missing env vars = silent death** | No validation at deploy | Fail-fast: startup script validates all REQUIRED vars |

---

### Golden Flows (Verified from V1)

#### Flow 1: Telegram → Claude → Response ✅ WORKING IN V1

```
1. User sends Telegram message
   └─ Webhook hits Caddy (HTTPS)
      └─ Caddy routes to n8n:5678
         └─ n8n workflow activates
            └─ Calls LLM via litellm
               └─ Response returns via Telegram Bot API

Critical Success Factors:
  • Webhook latency <3s (cold start = failure)
  • n8n workflow pre-activated (not activated on first call)
  • litellm healthy (UNHEALTHY = timeout)
```

**V2 Implementation:**
- VM ensures 0ms startup (no cold start)
- API activation with health check validation
- Pre-flight dependency check (litellm UP before n8n starts)

---

#### Flow 2: Secrets Distribution (GitOps Blocker #1)

```
V1 Broken Flow:
  Deploy → Manual n8n UI login → Import credentials → Hope nothing breaks

V2 Fixed Flow:
  Deploy → deployment/scripts/fetch_secrets.sh (GCP Secret Manager)
         → .env file created
         → Docker Compose mounts .env as env vars
         → n8n reads credentials from ENV (not DB)
         → Validation: List credentials API call (must show ≥1)
```

**V2 Implementation:**
- `deployment/scripts/fetch_secrets.sh` script with proper error handling
- Secrets injected at container startup (no UI import)
- Health gate: Deployment fails if credentials not accessible
- Evidence: [Slice 2A Runbook](docs/phase-2/slice-02a_runbook.md) documents full flow

---

## 📍 Where We Are Now

### Current Infrastructure State (DEV Environment)

**GCP Project:** `project-38-ai`

| Component | Resource Name | Status | Details |
|-----------|---------------|--------|---------|
| **VM** | `p38-dev-vm-01` | ✅ RUNNING | e2-medium, us-central1-a |
| **Static IP** | `p38-dev-ip-01` | ✅ IN_USE | 136.111.39.139 |
| **Firewall Rules** | `p38-dev-allow-*` | ✅ ACTIVE | SSH (22), HTTP (80), HTTPS (443) |
| **Docker** | - | ✅ INSTALLED | v29.1.3, service running |
| **Docker Compose** | - | ✅ INSTALLED | v5.0.0 |
| **Service Account (n8n)** | `n8n-runtime@...` | ✅ ATTACHED | Access to 3 secrets verified |
| **Service Account (kernel)** | `kernel-runtime@...` | ✅ CREATED | Access to 4 secrets verified |
| **Service Account (CI/CD)** | `github-actions-deployer@...` | ✅ CREATED | Access to all 7 secrets |
| **N8N Workflows** | - | ✅ ACTIVE | POC-02 (Telegram), POC-03 (Conversation Flow) |
| **GitHub App** | `project-38-scribe` | ✅ ACTIVE | App ID 2497877, webhook verified |
| **Cloud Run** | `github-webhook-receiver` | ✅ ACTIVE | IssueOps commands (/label, /assign, ACK) |
| **Observability** | Alert Policies (3) | ✅ ENABLED | Notification channel verified (Gate A) |

**Evidence:** [Slice 1 Execution Log](docs/phase-2/slice-01_execution_log.md)

---

### Secrets Inventory (Both Environments)

**Total:** 7 secrets × 2 projects (DEV + PROD) = 14 secret instances  
**Versions:** Each secret has 2 ENABLED versions (rotation capability)

| Secret Name | Used By | Purpose |
|-------------|---------|---------|
| `n8n-encryption-key` | n8n-runtime | n8n data encryption |
| `postgres-password` | n8n-runtime | Database credentials |
| `telegram-bot-token` | n8n-runtime | Telegram bot integration |
| `openai-api-key` | kernel-runtime | OpenAI API access |
| `anthropic-api-key` | kernel-runtime | Claude API access |
| `gemini-api-key` | kernel-runtime | Gemini API access |
| `github-pat` | kernel-runtime | GitHub integration |

**Status:** SYNC_OK / FINAL_OK — ready for use, no changes needed.

---

### Progress Tracker

#### ✅ COMPLETED

**Phase 1: Analysis & Planning**
- ✅ AIOS V1 mapping analyzed ([patterns_anti_patterns.md](docs/phase-1/patterns_anti_patterns.md))
- ✅ Gate A decision: VM-first strategy ([gateA_vm_first.md](docs/phase-1/gateA_vm_first.md))
- ✅ Least privilege IAM designed (3 service accounts)
- ✅ SSOT protocol established (Drive deprecated)

**Phase 2: Infrastructure**
- ✅ **Slice 1 DONE** (2025-12-15, 4min 30sec):
  - VM provisioned (`p38-dev-vm-01`)
  - Docker installed (v29.1.3)
  - IAM access verified (n8n-runtime can access 3 secrets)
  - Evidence pack captured with SHA256 verification
  - [Execution Log](docs/phase-2/slice-01_execution_log.md)

- ✅ **Slice 2A DONE** (2025-12-16):
  - N8N + PostgreSQL deployed (Docker Compose)
  - 3 secrets injected via Secret Manager
  - SSH tunnel access verified (localhost:5678)
  - [Execution Log](docs/phase-2/slice-02a_execution_log.md)

- ✅ **POC-01 PASS** (2025-12-18):
  - N8N headless activation verified
  - Workflow activation via API
  - [Evidence](docs/evidence/2025-12-18_poc01_pass.txt)

- ✅ **POC-02 PASS** (2025-12-18):
  - Telegram webhook integration verified
  - Fast-ACK pattern (48-213ms response)
  - [Evidence](docs/evidence/2025-12-18_poc02_pass.txt)

- ✅ **IssueOps Control (2025-12-20 - 2025-12-21)**:
  - GitHub App (project-38-scribe) configured
  - Cloud Run webhook receiver deployed
  - Commands: /label, /assign, ACK
  - Observability: 3 alert policies, verified notification channel (Gate A)
  - Control Room Issue #24 established
  - [SYSTEM_MAP.md](docs/_system/SYSTEM_MAP.md)

#### 📋 PLANNED (Documentation Ready, Awaiting Approval)

_(Moved to "NEXT DECISION" section - see Control Room Issue #24)_

#### ⏸️ DEFERRED (Pending Decisions)

**Slice 2B/3: Kernel Deployment**
- **Blocker:** Service account architecture decision
  - Option 1: Separate VM with kernel-runtime SA
  - Option 2: Multi-SA support on same VM
  - Option 3: Credential file approach (less preferred)
- **Dependencies:** Slice 2A must complete first

**Advanced Infrastructure (Phase 3)**
- Cloud SQL (managed Postgres)
- Custom VPC with Cloud NAT
- litellm migration to Cloud Run
- Load balancing for horizontal scaling
- **Trigger:** Only if VM baseline hits scaling limits or ops burden

---

## 🛠️ Operating Model

### Core Principles

#### 1. Truth Protocol (Evidence-First)

**Rule:** All claims must be verifiable from documented sources.

**Forbidden:**
- ❌ "I think the VM has 4GB RAM" → Not verified
- ❌ "The secrets probably work" → Not tested
- ❌ "It should be running" → Not confirmed

**Required:**
- ✅ "VM has 4GB RAM (verified: gcloud compute instances describe)"
- ✅ "Secrets accessible (verified: IAM policy shows n8n-runtime has secretAccessor role)"
- ✅ "Docker running (verified: systemctl status docker shows active)"

**Evidence Standard:**
- Every infrastructure change → captured in execution log
- Every command → full output preserved (redacted if needed)
- Every artifact → SHA256 hash in manifest
- No "trust me" — show the evidence

---

#### 2. Approval Gates (No Auto-Progression)

**Rule:** Each slice requires explicit approval before execution.

**Examples:**
- ✅ User says: **"Execute Slice 2A"** → Claude proceeds
- ❌ User says: "Sounds good" → Claude asks: "Confirm: Execute Slice 2A?"
- ❌ User says: "Let's deploy" → Claude asks: "Which slice? Slice 2A or Slice 2B?"

**Why It Matters:**
- Prevents runaway automation
- Forces review of documentation before action
- Ensures user understands blast radius
- Allows checkpoint verification between slices

---

#### 3. Least Privilege (No Shortcut Permissions)

**Rule:** Each service account gets minimal required access, no exceptions.

**Examples:**
- ✅ n8n-runtime gets 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token)
- ❌ n8n-runtime does NOT get openai-api-key (that's kernel's job)
- ✅ kernel-runtime gets 4 secrets (LLM APIs + github-pat)
- ❌ kernel-runtime does NOT get postgres-password (that's n8n's job)

**Verification:**
- Before each deployment: IAM policy check
- After each deployment: Verify service can't access forbidden secrets
- Evidence: IAM policy outputs in execution logs

---

#### 4. Git-Native Workflow (Repo = Truth)

**Rule:** All state, decisions, and documentation live in the repository.

**Structure:**
```
project-38/
├── PROJECT_NARRATIVE.md          ← You are here (entry point)
├── docs/
│   ├── context/                  ← Source of truth
│   │   ├── project_facts.md      ← Immutable facts (GCP projects, repos, paths)
│   │   ├── operating_rules.md    ← Operational protocols
│   │   ├── phase_status.md       ← Current progress
│   │   └── session_start_packet.md ← New session bootstrap
│   ├── phase-1/                  ← Planning & analysis
│   │   ├── gateA_vm_first.md     ← VM vs Cloud Run decision
│   │   └── patterns_anti_patterns.md ← V1 lessons learned
│   ├── phase-2/                  ← Deployment artifacts
│   │   ├── slice-01_runbook.md   ← Step-by-step execution plans
│   │   ├── slice-01_execution_log.md ← Evidence of what happened
│   │   ├── slice-01_rollback_plan.md ← How to undo
│   │   └── slice-02a_*.md        ← (planned) N8N deployment docs
│   └── evidence/
│       └── manifest.md           ← SHA256 hashes of external artifacts
└── traceability_matrix.md        ← Component status dashboard
```

**External Evidence Store (Not Committed):**
```
C:\Users\edri2\project_38__evidence_store\
├── phase-2/
│   ├── slice-01/                 ← RAW command outputs, logs, screenshots
│   └── slice-02a/                ← (future) N8N deployment evidence
```

**Benefits:**
- Every change tracked in Git history
- Rollback = `git revert`
- New sessions = read repo, not memory
- SHA256 hashes verify artifact integrity

**Drive Status:** DEPRECATED (no longer operational SSOT)

---

### Session Start Protocol

**Every new Claude session begins with:**

**Step 1:** Read [session_start_packet.md](docs/context/session_start_packet.md)

**Step 2:** Print 5-8 line snapshot:
```
📸 Snapshot:
✅ DONE: Slice 1 (VM + Docker + IAM)
📋 NEXT: Slice 2A (N8N deployment) — runbook ready, awaiting approval
⏸️ DEFERRED: Slice 2B (Kernel), Cloud SQL/NAT (optional)
🎯 Ready to: [analyze user request]
```

**Step 3:** Read core SSOT files:
- [project_facts.md](docs/context/project_facts.md)
- [operating_rules.md](docs/context/operating_rules.md)
- [traceability_matrix.md](docs/traceability_matrix.md)

**Step 4:** Await explicit user instruction (NO actions without approval)

---

### Critical Constraints

**⛔ NEVER DO:**

1. **Execute deployment without approval**
   - Slice 1 ✅ DONE
   - Slice 2A 📋 Awaiting "Execute Slice 2A"
   - Slice 2B/3 ⏸️ Not ready (architecture TBD)

2. **Run gcloud without `--project` flag**
   ```bash
   # ❌ WRONG
   gcloud compute instances list
   
   # ✅ CORRECT
   gcloud compute instances list --project=project-38-ai
   ```

3. **Recreate secrets or service accounts** (they're already DONE)

4. **Paste secret values anywhere** (metadata only)

5. **Write to legacy workspace** (`C:\Users\edri2\Desktop\AI\ai-os`) without explicit `LEGACY_WRITE_OK` keyword

6. **Deploy to PROD before DEV validation**

7. **Use Drive as SSOT** (it's deprecated)

**✅ ALWAYS DO:**

1. Print snapshot at session start
2. Verify facts before claims
3. Capture evidence for every infrastructure change
4. Update traceability matrix after completion
5. Request explicit approval before deployment

---

## 🧭 Next Steps & Decision Points

### Immediate Next Action

**Slice 2A: N8N + Postgres Deployment**

**What It Is:**
- Deploy n8n workflow engine (n8nio/n8n:latest)
- Deploy PostgreSQL database (postgres:16-alpine)
- Configure via Docker Compose (2 services only)
- Access via SSH port-forward (no firewall changes)

**Prerequisites:**
- ✅ Slice 1 complete (VM + Docker + IAM)
- ✅ Documentation ready (runbook, evidence pack, rollback plan)
- ✅ Service account verified (n8n-runtime has access to 3 secrets)

**Duration:** 20-30 minutes (estimated)

**Approval Required:** User must say **"Execute Slice 2A"**

**Documentation:**
- [Runbook](docs/phase-2/slice-02a_runbook.md) — Step-by-step execution
- [Evidence Pack](docs/phase-2/slice-02a_evidence_pack.md) — What to capture
- [Rollback Plan](docs/phase-2/slice-02a_rollback_plan.md) — How to undo

---

### Pending Decisions

**Decision 1: Kernel Deployment Architecture (Slice 2B/3)**

**Context:** Kernel service needs 4 secrets (LLM APIs + GitHub PAT), but current VM has n8n-runtime SA attached (only 3 secrets).

**Options:**
1. **Separate VM** with kernel-runtime SA (cleanest least-privilege)
2. **Multi-SA on same VM** (if GCP supports attaching multiple SAs)
3. **Credential file approach** (less preferred, manual secret management)

**Blocker:** Need to choose architecture before Slice 2B documentation

**Impact:** Determines Slice 2B runbook structure

---

**Decision 2: Advanced Infrastructure (Phase 3)**

**Context:** Current baseline is VM-only. Advanced infrastructure (Cloud SQL, VPC, Cloud Run) deferred.

**Trigger Points:**
- VM costs exceed $50/mo (need horizontal scaling)
- Manual ops burden blocks feature development
- Compliance requires managed services

**Do NOT trigger if:**
- Baseline still unstable (incident rate >1/week)
- Cost savings not justified (<$10/mo difference)
- Migration effort outweighs benefits

**Action:** Revisit after 3+ months of stable VM operations

---

## 📚 Key Documents Reference

### Entry Points (Start Here)
- **PROJECT_NARRATIVE.md** ← You are here
- [session_start_packet.md](docs/context/session_start_packet.md) ← New session bootstrap

### Source of Truth (SSOT)
- [project_facts.md](docs/context/project_facts.md) ← Immutable facts
- [operating_rules.md](docs/context/operating_rules.md) ← Operational protocols
- [phase_status.md](docs/context/phase_status.md) ← Current progress
- [traceability_matrix.md](docs/traceability_matrix.md) ← Component dashboard

### Strategic Decisions
- [gateA_vm_first.md](docs/phase-1/gateA_vm_first.md) ← VM vs Cloud Run
- [patterns_anti_patterns.md](docs/phase-1/patterns_anti_patterns.md) ← V1 lessons
- [ssot_and_evidence_protocol.md](docs/context/ssot_and_evidence_protocol.md) ← Repo-based workflow

### Execution Artifacts
- [slice-01_execution_log.md](docs/phase-2/slice-01_execution_log.md) ← VM baseline evidence
- [slice-02a_runbook.md](docs/phase-2/slice-02a_runbook.md) ← N8N deployment plan
- [Evidence Manifest](docs/evidence/manifest.md) ← SHA256 artifact verification

---

## 🎯 Success Metrics

**How We Know We're Winning:**

### Phase 1 ✅ COMPLETE
- [x] V1 pain points documented with root causes
- [x] Architecture decisions made with evidence-based rationale
- [x] Service account design completed (3 SAs, least privilege)
- [x] SSOT protocol established (repo-based, Drive deprecated)

### Phase 2 — In Progress
- [x] **Slice 1:** VM baseline deployed with Docker + IAM verified
- [ ] **Slice 2A:** N8N + Postgres deployed with zero manual credential import
- [ ] **Slice 2B/3:** Kernel deployed with separate SA architecture
- [ ] **Slice 3:** End-to-end workflow test (Telegram → Claude → Response)

### Phase 3 — Future
- [ ] 30+ days uptime with <1 incident/week
- [ ] Zero manual interventions for deployments
- [ ] Full GitOps: `git push` → automated deploy → health validated
- [ ] Rollback tested and verified (<5min recovery time)

---

## 💬 For New Team Members

### "I Just Joined — Where Do I Start?"

**5-Minute Orientation:**

1. **Read this document** (PROJECT_NARRATIVE.md) — you just did ✅
2. **Check current status:** [traceability_matrix.md](docs/traceability_matrix.md)
3. **Understand the rules:** [operating_rules.md](docs/context/operating_rules.md)
4. **See what's built:** [slice-01_execution_log.md](docs/phase-2/slice-01_execution_log.md)

**Ready to contribute?**
- Ask: "What's the next Slice status?" (current: Slice 2A awaiting approval)
- Read: Slice 2A [runbook](docs/phase-2/slice-02a_runbook.md)
- Wait: Explicit approval required before execution

### "Why Are We Being So Careful?"

**Because V1 taught us:**
- Manual clicks = no GitOps
- Silent failures = false confidence
- Drift = debugging nightmares
- No evidence = tribal knowledge

**V2 principles:**
- Infrastructure-as-Code (every resource traceable)
- Infrastructure-as-Evidence (every change documented)
- Least Privilege (minimize blast radius)
- Approval Gates (prevent runaway automation)

**Trade-off:** Slower execution, higher confidence.

**Payoff:** Production system you can trust.

---

## 🔄 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-16 | Initial strategic narrative — comprehensive rebuild context | Claude (Session) |

---

## ✅ Approval & Next Steps

**This Document Status:** ✅ ACTIVE (entry point for all sessions)

**Current Phase:** Phase 2 — Infrastructure & Deployment  
**Current Slice:** Slice 1 ✅ DONE, Slice 2A 📋 PLANNED (awaiting "Execute Slice 2A")

**For Next Session:**
1. Read this document (PROJECT_NARRATIVE.md)
2. Read [session_start_packet.md](docs/context/session_start_packet.md)
3. Print snapshot (5-8 lines)
4. Await user instruction

**No actions without explicit approval.**

---

**Repository:** https://github.com/edri2or-commits/project-38  
**GCP DEV Project:** project-38-ai  
**GCP PROD Project:** project-38-ai-prod (mirror after DEV validation)

---

*End of Strategic Narrative*