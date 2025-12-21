# SYSTEM MAP — Project 38 IssueOps

**Last Updated:** 2025-12-21  
**Purpose:** Single entrypoint to understand project state, decisions, and control flow

---

## 🎯 What is IssueOps?

**IssueOps** = Operations through GitHub Issues

**How it works:**
- GitHub Issues = primary control plane
- All decisions, gates, state changes → recorded in Issues
- Issues → Commands (via comments) → Automation → Evidence → Back to Issues (closed loop)

**SSOT (Single Source of Truth):**
- **Control Room Issue:** [#24](https://github.com/edri2or-commits/project-38/issues/24) ← Main operational hub
- **This file:** Navigation map to all canonical sources
- **Principle:** If it's not in Control Room Issue or linked from SYSTEM_MAP, it's not canon

---

## 🏗️ Architecture Overview

### Command Flow

```
User → Control Room Issue (#24) → Comment (/command)
  ↓
GitHub Webhook (signed, delivered to Cloud Run)
  ↓
Cloud Run: github-webhook-receiver (signature verification)
  ↓
Parse Command → Security Check (owner-only) → Get Installation Token
  ↓
Execute via GitHub API (add label, assign user, etc.)
  ↓
Post Result Comment to Same Issue
  ↓
User sees result (no context switching)
```

### IssueOps Components

| Component | Type | Trigger | Actions | Status |
|-----------|------|---------|---------|--------|
| GitHub Actions | Workflow | `issue_comment.created` + `/approve` | Log approval gate | ✅ Active (skeleton) |
| Cloud Run Webhook | Service | `issue_comment.created` (any comment) | `/label`, `/assign`, ACK | ✅ Active (production) |
| N8N Workflows | Service | Telegram webhook | (not IssueOps) | ✅ Active (POC-02) |

---

## 📋 Supported Commands

### Via Cloud Run (github-webhook-receiver)

**Endpoint:** `https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook`

| Command | Syntax | Action | Security | Example |
|---------|--------|--------|----------|---------|
| `/label` | `/label <name>` | Add label(s) to Issue | Owner-only | `/label bug urgent` |
| `/assign` | `/assign @username` | Assign user(s) to Issue | Owner-only | `/assign @edri2or-commits` |
| ACK | (no `/` prefix) | Post acknowledgment comment | Any user | `Hello` → `ACK: received...` |

**Security:**
- HMAC-SHA256 signature verification (webhook secret)
- Idempotency (Firestore tracks `X-GitHub-Delivery` ID)
- Owner-only for commands (non-owners get 202 but no action)
- Bot guard (ignores comments from Bot users)

### Via GitHub Actions (ops-console.yml)

| Command | Syntax | Action | Status |
|---------|--------|--------|--------|
| `/approve` | `/approve [action]` | Log approval gate | Skeleton (logs only, no automation) |

**Workflow:** `.github/workflows/ops-console.yml`

---

## 📁 File Structure & Canon Status

### 🟢 Canon (SSOT - Authoritative)

| Path | Purpose | Update Frequency | Owner |
|------|---------|------------------|-------|
| **Control Room Issue #24** | **Primary decision log** | **Every decision/deployment** | **User + Claude** |
| `docs/_system/SYSTEM_MAP.md` | **This file** - navigation hub | Every structural change | Claude |
| `docs/context/phase_status.md` | Current phase, gates, next steps | Every phase transition | Claude |
| `docs/context/project_facts.md` | Immutable project facts | Rarely (corrections only) | Claude |
| `docs/context/operating_rules.md` | Operating procedures & constraints | When rules change | Claude |
| `docs/traceability_matrix.md` | Decisions → Implementation tracking | After each decision | Claude |
| `docs/evidence/YYYY-MM-DD_*.txt` | RAW proof of execution | Every deployment/test | Claude |
| `docs/adr/ADR-NNN_*.md` | Architecture Decision Records | Per decision | Claude |

### 🟡 Secondary (Reference/Work-in-Progress)

| Path | Purpose | Status |
|------|---------|--------|
| `docs/sessions/YYYY-MM-DD_*.md` | Session summaries | Historical record |
| `docs/phase-2/*.md` | POC documentation | Frozen after POC completion |
| `docs/state/current_state.md` | Infrastructure snapshot | ⚠️ DEPRECATED - migrate to phase_status.md |
| `/mnt/transcripts/*.txt` | Claude conversation archives | Auto-generated |

### 🔴 Generated/Temporary (Delete After Use)

| Path | Purpose | Lifespan |
|------|---------|----------|
| `C:\Users\edri2\project_38\*.txt` | Script outputs, temp files | Session-scoped |
| `C:\Users\edri2\project_38\*.json` | API responses, temp configs | Session-scoped |

---

## 🚦 Gates System

### What is a Gate?

**Gate** = Verification checkpoint before proceeding

**When to create:**
- Deployment has critical dependency
- Need proof of external system behavior (email, webhook, API)
- Rollback requires specific verification

**Closure criteria:**
- RAW proof (not synthetic)
- Reproducible (can be re-verified)
- Documented in evidence file

### Current Gates

| Gate | Status | Definition | Closure Date | Evidence |
|------|--------|------------|--------------|----------|
| **Gate A** | ✅ CLOSED | Notification channel email delivery E2E verified | 2025-12-21 | [2025-12-21_notification_channel_verification.txt](../evidence/2025-12-21_notification_channel_verification.txt) |
| **Gate B** | ✅ CLOSED | Cloud Run log format matches metric filters | 2025-12-20 | Session transcript 2025-12-20 |

### Gate Documentation Protocol

**When gate is created:**
1. Add to `phase_status.md` under current phase
2. Define closure criteria (specific, verifiable)
3. Post to Control Room Issue (#24)

**When gate is closed:**
1. Create evidence file in `docs/evidence/`
2. Update `phase_status.md` with closure date + evidence link
3. Post to Control Room Issue (#24) with evidence link
4. Update this SYSTEM_MAP if structural

---

## 🔧 Infrastructure Components

### GCP Projects

- **DEV:** `project-38-ai` (current)
- **PROD:** `project-38-ai-prod` (future)

### Services

**Cloud Run:**

| Service | URL | Purpose | Status |
|---------|-----|---------|--------|
| github-webhook-receiver | `https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app` | Process GitHub webhooks (IssueOps) | ✅ ACTIVE |

**Compute Engine:**

| VM | IP | Services | Access | Status |
|----|----|---------| -------|--------|
| p38-dev-vm-01 | 136.111.39.139 | N8N, PostgreSQL | SSH tunnel (localhost:5678) | ✅ RUNNING |

**Secrets (Secret Manager):**

- `github-app-private-key` - RSA key for App authentication
- `github-webhook-secret` - HMAC signature verification
- `postgres-password` - PostgreSQL root password
- `n8n-encryption-key` - N8N credential encryption
- `telegram-bot-token` - Telegram bot authentication

**Observability (Cloud Monitoring):**

- **Metrics (logs-based, 2):**
  - `webhook_5xx_errors` - Count of 5xx HTTP responses
  - `webhook_command_errors` - Count of command execution failures
  
- **Alert Policies (3):**
  - Webhook High 5xx Error Rate (ID: 17939154262393650707)
  - Webhook Command Execution Errors (ID: 3749356261847228670)
  - Webhook High Request Latency (ID: 9334277562526392075)
  
- **Notification Channel:**
  - Type: Email
  - Address: edri2or@gmail.com
  - Status: ✅ VERIFIED (Gate A closed)

### GitHub Integration

**App:** project-38-scribe

- **App ID:** 2497877
- **Client ID:** Iv23liR3bOoRpgq05oe9
- **Installation:** edri2or-commits account
- **Repository:** project-38 (single repo scope)
- **Webhook:** ✅ Active, signature-verified, idempotent (Firestore TTL: 24h)

**Permissions:**
- Actions: Read/Write
- Contents: Read/Write  
- Issues: Write
- Metadata: Read (automatic)

---

## 🔄 Change Control Process

### Documentation Changes

**Before creating ANY new file:**

1. ✅ Check if existing file can hold the content
2. ✅ Update `docs/_system/_registry.yml` with file metadata
3. ✅ Update this SYSTEM_MAP if structural
4. ✅ Post to Control Room Issue (#24) if decision-related

**Protocol:**
- ❌ No "orphan" docs (every doc linked from SYSTEM_MAP or registry)
- ❌ No duplicate content (merge into existing canon file)
- ✅ Evidence files are atomic (one file per event/deployment)

### Deployment Changes

**Never:**
- Direct commits to `main` branch
- Deploy without commit SHA traceability
- Change production alerts without Gate closure
- Deploy without Control Room Issue comment

**Always:**
1. Create PR with evidence links
2. Update `traceability_matrix.md` (decision → commit)
3. **Post deployment plan to Control Room Issue (#24)**
4. Wait for `/approve deploy-vN` comment
5. Deploy with canary strategy (10% → 100%)
6. **Post deployment evidence to Control Room Issue (#24)**
7. Update `phase_status.md` with new state

---

## 💬 "Chat אחד" Protocol

### Current State: MANUAL PROTOCOL ✅

**Objective:** User works only from Control Room Issue (#24)

**How it works:**

#### Stage 1: Manual Sync (TODAY)

**User workflow:**
1. User works in **Claude Desktop chat** (primary interface)
2. Claude **auto-posts summaries** to Control Room Issue (#24) after:
   - Gate closures
   - Deployments
   - Strategic decisions
   - Evidence creation
3. User **reviews in GitHub** (mobile/web)
4. User **approves via comment:** `/approve <action>`
5. Automation executes (webhook-receiver or Actions)

**Example:**
```
[Claude Desktop]
User: Deploy webhook-receiver v7 to production

Claude: 
1. Builds deployment plan
2. Posts plan to Issue #24:
   "## Deploy Plan - v7
    Steps: build → canary 10% → wait for /approve → 100%
    Reply `/approve deploy-v7` to continue"
3. Waits for approval

[GitHub Issue #24]
User: /approve deploy-v7

[Claude Desktop]
Claude: Sees approval, executes deployment, posts evidence to #24
```

**Discipline required:**
- ✅ Claude posts every significant action to #24
- ✅ User monitors #24 for status (GitHub mobile notifications)
- ✅ Evidence files always linked from #24 comments

**Benefits:**
- ✅ Works immediately (no new infrastructure)
- ✅ Establishes audit trail
- ✅ Single conversation thread in GitHub
- ❌ Requires manual sync from Claude

---

#### Stage 2: Automated Sync (FUTURE - Week 2)

**Enhancement:** Claude Desktop with GitHub API automation

**Changes:**
- Claude **auto-reads** Control Room Issue via API (polling every 60s)
- Claude **auto-writes** updates via API (no manual "post this")
- User can comment in #24 directly, Claude sees it

**Implementation:**
```python
# Claude Desktop with scheduled task
while True:
    comments = github.issue_read(issue_number=24, method="get_comments")
    new_commands = [c for c in comments if c.created_at > last_check]
    
    for cmd in new_commands:
        if cmd.body.startswith('/'):
            execute_command(cmd)
            github.add_issue_comment(24, f"✅ Executed: {cmd.body}")
    
    time.sleep(60)
```

**Benefits:**
- ✅ No manual sync needed
- ✅ User can work entirely from GitHub (mobile-friendly)
- ❌ Still requires Claude Desktop running

---

#### Stage 3: Kernel Bridge (FUTURE - Month 2)

**Architecture:**
```
Control Room Issue #24
  ↕ (GitHub webhook)
Kernel (Cloud Run service)
  ↕ (API calls)
Claude API, N8N workflows, GCP services
```

**Kernel responsibilities:**
1. Subscribe to Issue #24 via webhook
2. Parse commands/requests from comments
3. Execute actions (deploy, query GCP, trigger N8N)
4. Call Claude API for analysis/generation
5. Post results back to #24

**User experience:**
- User posts **only** in Issue #24
- Kernel + Claude respond automatically
- No Claude Desktop needed (fully serverless)

**Status:** ⏸️ DEFERRED (requires Kernel deployment + SA architecture)

---

### Recommendation: Start with Stage 1

**Why:**
- ✅ Functional today (no deployment blockers)
- ✅ Creates discipline (manual → automatic later)
- ✅ Audit trail from day 1
- ✅ Stage 2/3 can be added without breaking flow

**First action:** Create Issue #24, pin it, start posting there

---

## 🔗 Quick Links

### Primary (Daily Use)

- **Control Room:** [Issue #24](https://github.com/edri2or-commits/project-38/issues/24) ← **Start here for status**
- **Navigation:** [SYSTEM_MAP.md](SYSTEM_MAP.md) ← **You are here**
- **Current State:** [phase_status.md](../context/phase_status.md)
- **Decisions Log:** [traceability_matrix.md](../traceability_matrix.md)

### Infrastructure (Weekly Check)

- **GitHub App:** https://github.com/apps/project-38-scribe
- **Cloud Run:** https://console.cloud.google.com/run?project=project-38-ai
- **Secrets:** https://console.cloud.google.com/security/secret-manager?project=project-38-ai
- **Monitoring:** https://console.cloud.google.com/monitoring?project=project-38-ai

### Evidence (Per Deployment)

- **Evidence Files:** [docs/evidence/](../evidence/)
- **ADRs:** [docs/adr/](../adr/)
- **Sessions:** [docs/sessions/](../sessions/)

---

## 📝 Maintenance Rules

### This file must be updated when:

- ✅ New canon file created
- ✅ Gate added/closed
- ✅ Infrastructure component deployed
- ✅ Command/workflow added
- ✅ Change control process modified
- ✅ "Chat אחד" protocol changes

### Update process:

1. Edit this file
2. Commit: `docs: update SYSTEM_MAP - [reason]`
3. Post link to Control Room Issue (#24)
4. **No approval needed** (living document)

---

## 📊 Metrics (Self-Monitoring)

**Doc sprawl indicators:**
- Canon files: 8 (target: stable)
- Orphan docs: 0 (target: 0)
- Evidence files: 3 (target: growing)
- Temp files in root: 0 (target: 0)

**Last cleanup:** 2025-12-21  
**Next review:** 2025-12-28

---

**Version:** 2.0 (IssueOps-focused)  
**Created:** 2025-12-21  
**Last Updated:** 2025-12-21  
**Maintainer:** Claude for Project 38
