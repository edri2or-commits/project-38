# Decision Log — Project 38

## Format
Each entry includes: Date, Decision, Context, Rationale, Impact

---

## 2025-12-19: GitHub App Webhook — Production Deployment (Cloud Run)

**Context:**
- GitHub App "project-38-scribe" created with App ID 2497877
- Cloud Run service `github-webhook-receiver` deployed (us-central1)
- Firestore database provisioned for idempotency tracking
- Webhook URL: https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook

**Decision:**
Configure webhook URL with signature verification and idempotency (PR #15).

**Rationale:**
1. **Stable HTTPS Endpoint:** Cloud Run provides production-grade HTTPS with auto-scaling
2. **Security-First:** HMAC-SHA256 signature verification before processing (prevents delivery_id poisoning)
3. **Idempotency:** Firestore-based duplicate detection using X-GitHub-Delivery GUID
4. **Fast-ACK:** Return 202 immediately (48-213ms measured, well under 10s requirement)
5. **TTL:** Documents expire after 24h (automatic cleanup)

**Impact:**
- GitHub webhook events delivered automatically to Cloud Run
- Signature verification prevents unauthorized requests (401)
- Duplicate deliveries skipped gracefully (202 + log "duplicate skipped")
- Firestore costs: minimal (free tier covers expected load)

**Implementation:**
- PR #15: signature-first flow + Firestore idempotency + TTL
- Main SHA: ee50ab7f690e1b443a811046ceee4ba8bad4f0e1
- Revision: github-webhook-receiver-00006-n54
- All production gates passed (401/202/duplicate/logs/<10s)

**References:**
- Issue #14: https://github.com/edri2or-commits/project-38/issues/14
- PR #15: https://github.com/edri2or-commits/project-38/pull/15

**Supersedes:**
- Previous decision (2025-12-19): "Keep Disabled Until Stable HTTPS" → now has stable endpoint

---

## 2025-12-19: GitHub App Webhook — Keep Disabled Until Stable HTTPS

**Context:**
- GitHub App "project-38-scribe" created with App ID 2497877
- Webhook checkbox enabled in UI, but URL field empty
- No stable production HTTPS endpoint available

**Decision:**
Keep webhook enabled (checkbox checked) but URL unconfigured.

**Rationale:**
1. **No Stable Endpoint:** Current endpoints:
   - N8N: localhost:5678 (SSH tunnel only)
   - Telegram: Temporary Cloudflare Tunnel (not suitable for GitHub webhooks)
   - No production domain or Cloud Run deployment
2. **GitHub Behavior:** GitHub does not deliver webhook events without URL configured
3. **Future-Ready:** Checkbox enabled = ready to add URL when endpoint available
4. **API Still Works:** GitHub App API calls (JWT auth) function independently of webhooks

**Impact:**
- GitHub App usable via API (manual triggers, workflow dispatch)
- No automatic webhook events (push, issues, PR comments) until URL set
- When stable endpoint deployed: Add URL + webhook secret + implement signature verification

**Alternatives Considered:**
- Disable webhook entirely: Rejected (adds extra step when endpoint ready)
- Use temporary Cloudflare Tunnel: Rejected (unstable, conflicts with Telegram tunnel)
- Deploy Cloud Run immediately: Deferred (architecture decisions pending)

**Next Steps:**
1. Continue with POC-03 (Telegram conversation flow) OR IssueOps automation
2. Deploy stable HTTPS endpoint (domain registration OR Cloud Run with min-instances=1)
3. Configure webhook URL + secret in GitHub App settings
4. Implement signature verification in webhook handler

---

## 2025-12-19: IssueOps Workflow — Issues Only (Not PRs)

**Context:**
- Created `.github/workflows/ops-console.yml` with issue_comment trigger
- Initial version included PRs in scope
- Permissions included pull-requests:write

**Decision:**
Restrict workflow to issues only (exclude PRs) with minimal permissions.

**Rationale:**
1. **Clear Separation:** Issues = operational commands, PRs = code review workflow
2. **Least Privilege:** Only issues:write permission needed (dropped pull-requests:write, contents:read)
3. **Gate Clarity:** startsWith() more precise than contains() for command parsing

**Implementation:**
```yaml
if: |
  !github.event.issue.pull_request &&
  startsWith(github.event.comment.body, '/approve')
permissions:
  issues: write
```

**E2E Test:** ✅ Issue #10, workflow run ID 20353584659 (SUCCESS, 7s)

---

## 2025-12-18: GitHub App Creation — Single Repo Scope

**Context:**
- Need automation for repository operations (issues, workflows, commits)
- Multiple installation scope options available

**Decision:**
Install GitHub App to single repository (project-38) only.

**Rationale:**
1. **Principle of Least Privilege:** Limit blast radius
2. **Clear Scope:** Single project automation needs
3. **Easier Revocation:** Can uninstall without affecting other repos

**Permissions (Unverified - Awaiting UI Evidence):**
- Actions: R/W (workflow dispatch, re-run)
- Contents: R/W (commits, branches, files)
- Workflows: R/W (workflow file management)

*Verification URL:* https://github.com/settings/apps/project-38-scribe

---

**Future Decisions:**
- Slice 2B/3 architecture (SA deployment model)
- Production HTTPS strategy (domain vs Cloud Run)
- PROD environment mirror timing
