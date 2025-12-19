# Current State Snapshot — Project 38

**Last Updated:** 2025-12-19  
**Status:** Phase 2 Active (DEV environment operational)

---

## GitHub App: project-38-scribe

**Created:** 2025-12-18  
**Status:** ✅ ACTIVE

### Configuration
- **App ID:** 2497877
- **Client ID:** Iv23liR3bOoRpgq05oe9
- **Installation:** edri2or-commits account only
- **Repository:** project-38 (single repo scope)

### Permissions
**Status:** UNKNOWN (awaiting UI verification)

*To verify:* Visit https://github.com/settings/apps/project-38-scribe → Permissions & events

*Expected permissions (unverified):*
- Actions: Read/Write
- Contents: Read/Write
- Workflows: Read/Write
- Metadata: Read (automatic)

### Webhook Status
- **Active:** ✅ ACTIVE (configured and verified in production)
- **URL:** https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook
- **Secret:** ✅ Configured (stored in Secret Manager: github-webhook-secret)
- **Delivery:** ✅ Verified (ping + redeliver tests passed)

**Features:**
- Signature verification (HMAC-SHA256) before processing
- Idempotency via Firestore (X-GitHub-Delivery tracking)
- Fast-ACK: 202 responses in <10s (48-213ms measured)
- TTL: Documents expire after 24h (ACTIVE)

### Authentication
- **Method:** Private key (RSA)
- **Storage:** Local file (outside repository, in .gitignore)
- **API Access:** Full (via JWT → installation token exchange)

---

## IssueOps Workflow

**File:** `.github/workflows/ops-console.yml`  
**Status:** ✅ ACTIVE  
**Created:** 2025-12-19

### Configuration
```yaml
Trigger: issue_comment (created events)
Gate: startsWith(comment.body, '/approve')
Scope: Issues only (NOT pull requests)
Permissions: issues:write (least privilege)
```

### E2E Test Results
- **Issue:** #10 (E2E Test: Ops Console Workflow)
- **Comment:** /approve command posted
- **Workflow Run:** ✅ SUCCESS (ID: 20353584659, duration: 7s)
- **Trigger:** issue_comment event captured correctly

---

## Infrastructure Status

### DEV Environment (project-38-ai)

**VM:** p38-dev-vm-01
- IP: 136.111.39.139
- Type: e2-medium
- Region: us-central1

**Services:**
- ✅ N8N: Running (localhost:5678, SSH tunnel access)
- ✅ PostgreSQL: Running (healthy, production secrets)
- ✅ Telegram Webhook: Configured (temporary Cloudflare Tunnel)

**Secrets (GCP Secret Manager):**
- ✅ postgres-password (production)
- ✅ n8n-encryption-key (production)
- ✅ telegram-bot-token (production)

### HTTPS Endpoints

**Production (Cloud Run):**
- GitHub Webhook: https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook
  - Service: github-webhook-receiver
  - Revision: github-webhook-receiver-00006-n54
  - Region: us-central1
  - Status: ✅ ACTIVE (signature-verified, idempotent)

**Development:**
- Telegram: Temporary Cloudflare Tunnel (https://count-allowing-licensing-demands.trycloudflare.com)

---

## Phase Status

### ✅ Completed
- Phase 1: Pre-Build (GCP projects, secrets, IAM)
- Slice 1: VM Baseline
- Slice 2A: N8N Deployment
- POC-01: Headless Activation + Hardening
- POC-02: Telegram Webhook Integration
- GitHub App: Created and configured
- IssueOps: Workflow skeleton deployed

### 📋 Next
- POC-03: Full Conversation Flow (workflows imported, activation blocked)
- GitHub App webhook: Configure when stable HTTPS available

### ⏸️ Deferred
- Slice 2B/3: Kernel Deployment (SA architecture TBD)
- Production HTTPS (domain + Let's Encrypt or Cloud Run)
- PROD environment mirror

---

## Decision Summary

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-18 | GitHub App created with webhook enabled | Cloud Run provides stable HTTPS endpoint |
| 2025-12-19 | Webhook configured and verified in production | PR #15: signature-first + idempotency + TTL |
| 2025-12-19 | IssueOps workflow: Issues only (not PRs) | Clear separation of concerns; least privilege |

---

## Known Gaps

1. **POC-03 Activation:** Workflows imported but not properly activated
2. **Telegram Credentials:** Need to be created in n8n for POC-03
3. **Production HTTPS:** No permanent domain or SSL certificate (Cloud Run provides stable HTTPS)
4. **GitHub Webhook Infrastructure:** Firestore + Cloud Run operational; future: add processing logic beyond ACK

---

**Next Session:** Continue with POC-03 activation OR develop IssueOps automation logic
