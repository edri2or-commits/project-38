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
- **Active:** ✓ Enabled (checkbox checked in UI)
- **URL:** Empty (not configured)
- **Secret:** Empty (not configured)
- **Delivery:** None (GitHub does not deliver events without URL)

**Rationale:** No stable HTTPS endpoint exists. Webhook remains enabled for future use but URL not set until production endpoint deployed.

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

**Available:**
- Telegram: Temporary Cloudflare Tunnel (https://count-allowing-licensing-demands.trycloudflare.com)

**Not Available:**
- GitHub App webhooks: No stable HTTPS endpoint
- Production domain: DEFERRED

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
| 2025-12-18 | GitHub App created without webhook URL | No stable HTTPS endpoint; webhook can be added later |
| 2025-12-19 | Webhook remains enabled but unconfigured | Ready for future use when endpoint deployed |
| 2025-12-19 | IssueOps workflow: Issues only (not PRs) | Clear separation of concerns; least privilege |

---

## Known Gaps

1. **GitHub App Webhooks:** Enabled but URL not set (waiting for stable endpoint)
2. **POC-03 Activation:** Workflows imported but not properly activated
3. **Telegram Credentials:** Need to be created in n8n for POC-03
4. **Production HTTPS:** No permanent domain or SSL certificate

---

**Next Session:** Continue with POC-03 activation OR develop IssueOps automation logic
