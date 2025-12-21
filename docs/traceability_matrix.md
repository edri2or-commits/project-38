---

## Detailed Status: Stage 2B - LLM Integration via OIDC/WIF

### Status: ✅ DONE (Gate 2B CLOSED - 2025-12-21)

**Execution Status:** ✅ COMPLETE  
**Documentation:**
- [Evidence File](evidence/2025-12-21_stage_2b_llm_e2e.txt)
- [Control Room Comment](https://github.com/edri2or-commits/project-38/issues/24#issuecomment-3679664969)

**Objective:** LLM-powered IssueOps with OIDC/WIF security (zero GitHub Secrets)

**Implementation:**
- **Approach:** GitHub Actions + OIDC to GCP Secret Manager
- **Workflow:** `.github/workflows/llm-bot-stage2b.yml`
- **PR:** #30 (Squash merged)
- **Commit:** c6b79d4
- **Deployment:** Merged to main 2025-12-21

**Security Architecture:**
1. **OIDC/WIF Authentication:**
   - Workload Identity Pool: github-actions-pool
   - Provider: github-actions-provider
   - Service Account: github-actions-llm@project-38-ai.iam.gserviceaccount.com
   - Short-lived credentials (no static secrets)
   - Attribute Condition: repository == 'edri2or-commits/project-38'

2. **Secret Manager Access:**
   - OPENAI_API_KEY: project-38-ai/openai-api-key
   - ANTHROPIC_API_KEY: project-38-ai/anthropic-api-key
   - GEMINI_API_KEY: project-38-ai/gemini-api-key
   - Runtime retrieval (not stored in GitHub)
   - IAM Role: roles/secretmanager.secretAccessor

3. **Command Injection Prevention:**
   - Line 51: `BODY=$(jq -r '.comment.body' "$GITHUB_EVENT_PATH")`
   - Line 126: Python `json.load(GITHUB_EVENT_PATH)`
   - ✅ NO heredoc with untrusted input
   - ✅ NO bash string interpolation of user content

4. **Access Control:**
   - Lines 28-44: author_association check
   - Allowed: OWNER, MEMBER only
   - Blocked: CONTRIBUTOR, FIRST_TIME_CONTRIBUTOR, NONE
   - ✅ Public repo protection (cost abuse prevention)

**Guard Order (3 gates):**
1. **Bot Guard:** Skip Bot users (prevent loops)
2. **Access Control:** OWNER/MEMBER only (NEW in Stage 2B)
3. **Command Guard:** /ask or /plan only

**Permissions:**
- `id-token: write` (OIDC to GCP)
- `issues: write` (Post comments)
- `contents: read` (Checkout repo)

**Trigger:**
- Event: `issue_comment.created`
- Scope: Issue #24 only
- Commands: `/ask` or `/plan`

**Gate 2B Verification:**
- **Test Command:** Comment #3679660658
  - User: edri2or-commits
  - Body: `/ask What is the current phase status?`
  
- **LLM Response:** Comment #3679660787
  - User: github-actions[bot]
  - Model: claude-sonnet-4-20250514
  - Max Tokens: 1000
  
- **Workflow Run:** https://github.com/edri2or-commits/project-38/actions/runs/20417158558
  - Status: success
  - Duration: ~30 seconds
  
- **OIDC Authentication:** ✅ VERIFIED
  - Credentials file: /home/runner/work/project-38/project-38/gha-creds-a8938b6414bb8e01.json
  - Project: project-38-ai
  
- **Secret Access:** ✅ VERIFIED
  - All 3 API keys retrieved from Secret Manager
  - Secrets properly masked in logs (*** format)
  - No secret values exposed

**Context Loading:**
- docs/_system/SYSTEM_MAP.md (2000 chars truncated)
- docs/context/phase_status.md (2000 chars truncated)
- Loaded into system prompt for LLM

**LLM Configuration:**
- Provider: Anthropic
- Model: claude-sonnet-4-20250514
- Max Tokens: 1000
- API Version: 2023-06-01
- System Prompt: Project 38 IssueOps assistant (with SSOT context)

**Response Format:**
```markdown
🤖 **LLM Response** (Claude Sonnet 4)

{response_text}

---
*Command: `/ask`*
*Model: claude-sonnet-4-20250514*
<!-- P38_LLM_RESPONSE -->
```

**Verification Results:**
- ✅ Bot Guard: Echo Bot ACK (#3679660747) did NOT trigger LLM workflow
- ✅ Access Control: OWNER permission verified for edri2or-commits
- ✅ Command Guard: /ask command detected and processed
- ✅ OIDC Auth: Short-lived token obtained successfully
- ✅ Secret Manager: All 3 keys retrieved without errors
- ✅ Secrets Masking: Verified in workflow logs
- ✅ LLM API Call: Anthropic API responded successfully
- ✅ Response Posted: Comment created in Issue #24
- ✅ Loop Prevention: LLM response did not trigger new workflow run

**Security Validation:**
- ❌ NO command injection vectors found
- ❌ NO heredoc with untrusted input
- ❌ NO GitHub Secrets used (100% runtime secret access)
- ✅ GITHUB_EVENT_PATH used for all user input
- ✅ Access control enforced at workflow level
- ✅ Secrets never logged or exposed

**Evidence:**
- Full E2E test log: [2025-12-21_stage_2b_llm_e2e.txt](evidence/2025-12-21_stage_2b_llm_e2e.txt)
- SHA256: A667006885C6744F1B0169EA9C3A222D8CD8F0E72A2C3481DDDC2ECFE40A05FF
- Verification checklist: All items ✅
- Zero security exceptions in logs

**Comparison: Stage 2A vs 2B:**
| Feature | Stage 2A (Echo Bot) | Stage 2B (LLM Integration) |
|---------|---------------------|----------------------------|
| Authentication | GITHUB_TOKEN only | GITHUB_TOKEN + OIDC to GCP |
| Secrets | None | 3 from Secret Manager |
| Guards | 3 (Issue, Bot, Echo Marker) | 3 (Bot, Access, Command) |
| Complexity | Low (Echo ACK) | High (LLM API + Context) |
| Security Risk | Low | Medium (mitigated) |
| Access Control | None (any commenter) | OWNER/MEMBER only |

**Gate 2B Status:** ✅ CLOSED
- Deployed: 2025-12-21T23:05:36Z (merge)
- Verified: 2025-12-21T23:06:07Z (E2E test)
- Evidence: docs/evidence/2025-12-21_stage_2b_llm_e2e.txt

**Next Steps:**
- Ready for POC-03: Full Conversation Flow
- OR: Expand LLM capabilities (additional commands, context sources)

**Action Required:** None — LLM integration operational in production

## Detailed Status: Infrastructure (Slice 1 - VM Baseline)

### Status: ✅ DONE (Executed 2025-12-15)

**Execution Status:** ✅ COMPLETE  
**Documentation:**
- [Runbook](phase-2/slice-01_runbook.md) — Step-by-step execution plan
- [Execution Log](phase-2/slice-01_execution_log.md) — Full execution evidence (4min 30sec)
- [Evidence Pack](phase-2/slice-01_evidence_pack.md) — Evidence capture requirements
- [Rollback Plan](phase-2/slice-01_rollback_plan.md) — Cleanup procedures

**Approach:** VM-first minimal (no managed services initially)

**Completed Components:**
- ✅ Single Compute Engine VM (e2-medium): `p38-dev-vm-01`
- ✅ External static IP address: `p38-dev-ip-01` (136.111.39.139)
- ✅ Firewall rules: SSH (22), HTTP (80), HTTPS (443)
- ✅ Docker 29.1.3 + Docker Compose 5.0.0 installed on VM
- ✅ VM Service Account: `n8n-runtime@project-38-ai.iam.gserviceaccount.com` attached
- ✅ Secret access validated: n8n-runtime has IAM access to its 3 secrets (metadata verified)

**Execution Details:**
- **Duration:** 4 minutes 30 seconds
- **Date:** 2025-12-15
- **Strategy:** Skipped apt-get upgrade, used direct Docker installation (avoided timeout issues)
- **All commands:** Used `--project project-38-ai` flag
- **Environment:** DEV only (project-38-ai)

**Evidence:**
- Full execution log: [slice-01_execution_log.md](phase-2/slice-01_execution_log.md)
- RAW outputs included (with secret redaction)
- Verification checks: All passed ✅

**Next Steps:**
- Ready for Slice 2: Workload Deployment (N8N + Kernel services)

---

## Detailed Status: Advanced Infrastructure (Optional/Deferred)

### Status: ⏸️ OPTIONAL/DEFERRED (Phase 2B or 3)

**When to Consider:**
- If scaling beyond single VM is required
- If managed database (Cloud SQL) becomes necessary
- If private networking (no external IPs) is mandated
- If high availability is needed

**Components:**
- Custom VPC with subnets
- Cloud NAT (for private VM internet access)
- Cloud SQL PostgreSQL (managed database)
- Load balancing (for multiple VMs)
- VPC peering or VPN (for hybrid connectivity)

**Prerequisites for Advanced Infrastructure:**
- ✅ Slice 1 (VM Baseline) must be complete and validated
- ✅ User decision to proceed with advanced setup
- ✅ Cost-benefit analysis documented

**Action Required:** Not needed initially — decision deferred until VM baseline is validated

---

## Detailed Status: Workload Deployment (Slice 2A - N8N Only)

### Status: ✅ DONE (Executed 2025-12-16)

**Execution Status:** ✅ COMPLETE  
**Documentation:**
- [Runbook](phase-2/slice-02a_runbook.md) — Step-by-step execution plan
- [Execution Log](phase-2/slice-02a_execution_log.md) — Full execution evidence (~72 minutes)
- [Evidence Pack](phase-2/slice-02a_evidence_pack.md) — Evidence capture requirements
- [Rollback Plan](phase-2/slice-02a_rollback_plan.md) — Cleanup procedures

**Split Decision:** Slice 2 split into 2A (N8N) + 2B/3 (Kernel) for least privilege compliance

**Scope (Slice 2A):**
- Deploy N8N workflow engine (n8nio/n8n:latest)
- Deploy PostgreSQL database (postgres:16-alpine)
- Use Docker Compose (2 services only)
- Access via SSH port-forward (localhost:5678 → VM:5678)
- **Secrets:** 3 only (n8n-encryption-key, postgres-password, telegram-bot-token)
- **Service Account:** n8n-runtime (has access to 3 secrets only)

**Completed Components:**
- ✅ N8N workflow engine deployed (n8nio/n8n:latest)
- ✅ PostgreSQL database deployed (postgres:16-alpine)
- ✅ Docker Compose orchestration (2 services)
- ✅ 3 secrets fetched at runtime from Secret Manager
- ✅ SSH port-forward established (localhost:5678 → VM:5678)
- ✅ Health checks passing (Postgres + N8N API)
- ✅ Security: Port 5678 bound to localhost only, zero firewall changes

**Execution Details:**
- **Duration:** ~72 minutes (including image pulls and verification)
- **Date:** 2025-12-16
- **Strategy:** Runtime secret injection, SSH tunnel for UI access
- **All commands:** Used `--project project-38-ai` flag
- **Environment:** DEV only (project-38-ai)

**Resources Created:**
- Containers: p38-postgres, p38-n8n
- Network: edri2_project38-network (bridge)
- Volumes: edri2_postgres_data, edri2_n8n_data
- UI Access: http://localhost:5678 (via SSH tunnel)

**Evidence:**
- Full execution log: [slice-02a_execution_log.md](phase-2/slice-02a_execution_log.md)
- RAW outputs included (with secret redaction)
- Verification checks: All passed ✅

**Rationale for Split:**
1. **Least Privilege:** n8n-runtime SA has IAM access to only 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token)
2. **Kernel requires 4 additional secrets:** openai-api-key, anthropic-api-key, gemini-api-key, github-pat
3. **Cannot deploy Kernel with n8n-runtime SA** (would violate least privilege or require SA changes)
4. **Networking:** SSH port-forward approach (no firewall changes, secure encrypted tunnel)

**Next Steps:**
- Ready for Slice 2B/3: Kernel deployment (SA architecture decision required)
- OR proceed to Slice 3: Testing & validation (N8N only)

---

## Detailed Status: POC-01 (Headless Activation + Hardening)

### Status: ✅ PASS (Executed 2025-12-16)

**Documentation:** [poc-01_headless_hardening.md](phase-2/poc-01_headless_hardening.md)

**Verified:**
- ✅ Workflow import via CLI (`n8n import:workflow`)
- ✅ Headless activation (workaround for CLI bug)
- ✅ Webhook responds HTTP 200 without UI
- ✅ Security hardening active (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`, `NODES_EXCLUDE`)

**Key Discovery:**
- `active=true` is NOT enough — requires `activeVersionId` + `workflow_history` record
- CLI bug: `n8n publish:workflow` fails on imported workflows
- Workaround script: `deployment/n8n/scripts/n8n-activate.sh`

---

## Detailed Status: POC-02 (Telegram Webhook Integration)

### Status: ✅ PASS (Executed 2025-12-16)

**Documentation:** [poc-02_telegram_webhook.md](phase-2/poc-02_telegram_webhook.md)

**Verified:**
- ✅ Cloudflare Tunnel for HTTPS (`https://count-allowing-licensing-demands.trycloudflare.com`)
- ✅ Telegram setWebhook + getWebhookInfo
- ✅ n8n receives updates (execution evidence: ID #19, status=success)
- ✅ Basic update_id deduplication (in-memory)

**Infrastructure:**
- Workflow ID: `fyYPOaF7uoCMsa2U`
- Webhook Path: `/webhook/telegram-v2`

**Limitations (Production):**
- Cloudflare Tunnel = temporary (URL changes on restart)
- In-memory dedup = lost on restart
- Production needs: Domain+SSL, Redis/Postgres dedup

---

## Detailed Status: Workload Deployment (Slice 2B/3 - Kernel)

### Status: ⏸️ DEFERRED (Pending SA Architecture Decision)

**Scope:**
- Deploy Kernel/Agent service (FastAPI backend)
- **Secrets:** 4 (openai-api-key, anthropic-api-key, gemini-api-key, github-pat)
- **Service Account:** kernel-runtime (has access to 4 LLM/integration secrets)

**Options for Deployment:**
1. **Separate VM** with kernel-runtime SA (cleanest least-privilege approach)
2. **Multi-SA on same VM** (if GCP supports attaching multiple SAs)
3. **Credential file approach** (less preferred, manual secret management)

**Decision Required:** User to choose SA architecture approach

**Dependencies:**
- ✅ Slice 2A complete (N8N validated)
- ❌ SA architecture decision

**Action Required:** Not ready until architecture finalized

---

## Detailed Status: Testing & Validation (Slice 3)

### Status: 📋 NEXT

**Scope:**
- Smoke tests for all services
- Secret access validation
- Logging verification
- End-to-end workflow testing

**Dependencies:**
- ❌ Workload Deployment (Slice 2) must be complete

**Action Required:** Cannot start until Slice 2 is done

---

## Detailed Status: PROD Mirror (Slice 4)

### Status: ⏸️ DEFERRED

**Scope:**
- Mirror DEV infrastructure to PROD (project-38-ai-prod)
- Deploy workloads to PROD
- Validate PROD environment
- Cutover from legacy AIOS (if applicable)

**Dependencies:**
- ❌ Testing & Validation (Slice 3) must pass
- ❌ User approval required

**Action Required:** Cannot start until DEV is fully validated and approved

---

## Risk Register

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Secret value exposure | 🔴 High | Strict no-paste policy + documentation | ✅ Mitigated |
| Wrong GCP project | 🔴 High | Mandatory --project flag rule | ✅ Mitigated |
| Legacy workspace corruption | 🟡 Medium | READ-ONLY quarantine + LEGACY_WRITE_OK keyword | ✅ Mitigated |
| Premature PROD deploy | 🔴 High | DEV-first approach + explicit approval gate | ✅ Mitigated |
| IAM over-permission | 🟡 Medium | Least privilege matrix documented | ✅ Mitigated |

---

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-12-15 | Use 2 ENABLED versions per secret | Redundancy + rotation capability | Secrets: FINAL_OK |
| 2025-12-15 | Least privilege IAM matrix | Security best practice | IAM: IAM_OK |
| 2025-12-15 | Legacy workspace READ-ONLY by default | Prevent accidental changes | Operating rules established |
| 2025-12-15 | DEV-first approach | Validate before PROD | Slice progression defined |
| 2025-12-15 | Drive update requests (no auto-sync) | Manual approval for Drive changes | Drive update workflow defined |
| 2025-12-15 | VM-first minimal baseline (Slice 1) | Start simple, scale later if needed | Cloud SQL/NAT/VPC deferred to Phase 2B/3 |
| 2025-12-15 | Split Slice 2 → Slice 2A (N8N) + Slice 2B/3 (Kernel) | **Least Privilege Compliance:** n8n-runtime SA has access to only 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token). Kernel needs 4 additional secrets (openai-api-key, anthropic-api-key, gemini-api-key, github-pat) requiring different SA. **Networking:** SSH port-forward avoids opening port 5678 in firewall. | Slice 2A: 2 services (postgres, n8n), 3 secrets, SSH access. Slice 2B/3: Kernel deferred pending SA architecture decision. |
| 2025-12-15 | Drive deprecated; SSOT moved to repo; Evidence external with manifest+hashes | **Drift Prevention:** Eliminate sync lag between Drive and repo. **Git-Native Workflow:** All state/decisions tracked in Git for full audit trail and easy rollback. **Evidence Integrity:** SHA256 hashes in manifest verify artifact authenticity without committing large files. **Session Continuity:** New sessions start from repo state via `session_start_packet.md`, not memory or Drive paste. **External Evidence Store:** Large artifacts (logs, screenshots, binaries) stored at `<EVIDENCE_STORE_PATH>\` and referenced via `docs/evidence/manifest.md` with SHA256 verification. | Repo = SSOT (`docs/context/` files + traceability matrix). Drive = DEPRECATED. Evidence store = external (not committed). Manifest = integrity bridge (SHA256 hashes). Session start = `session_start_packet.md` template. No Drive sync needed. |
| 2025-12-16 | Security-reviewed deployment scripts committed | 4 automation scripts added to repo with full security review: **deployment/scripts/fetch_secrets.sh** (SECRET_FETCHER with parameterized PROJECT_ID + all 7 secrets), **deployment/archive/startup.sh** (VM bootstrap with auto-detected user), **p38_sync_secrets.ps1** (PowerShell secret sync), **gpt_google_workspace_schema.yaml** (OpenAPI schema with URL placeholder). All hardcoded secrets/URLs removed. Pre-commit scanning performed. | Scripts ready for Phase 2 deployment. All secrets injected at runtime from Secret Manager (zero hardcoded values). |
| 2025-12-18 | Created GitHub App (project-38-scribe) | **Granular Automation:** Actions/Contents/Workflows R/W only (least privilege). **Repository-Scoped:** Limited to project-38 (isolated from other repos). **Auditability:** All actions attributed to "project-38-scribe[bot]" (clear audit trail). **Revocable:** Can uninstall without affecting other tools. **No Webhook:** Disabled (no stable HTTPS endpoint yet, can add later). | GitHub App ready for automation: documentation updates, workflow dispatch, CI/CD orchestration. Private key stored at `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem` (outside repo). Documentation in `docs/github-app/`. |
| 2025-12-20 | Canary deployment for Command Parsing MVP | **Progressive Rollout:** 10% → 100% traffic migration minimizes blast radius. **Multi-Gate Validation:** Traffic state + error logs + real webhook test at each phase. **Zero Downtime:** Traffic routing without service interruption. **Rollback Capability:** Previous revision preserved for instant rollback. **Real-World Testing:** Live GitHub webhook verification before full deployment. | Command parsing MVP (/label, /assign) deployed to production via Cloud Run revision 00009-lfb. Zero errors detected. Rollback procedure documented. Session brief in `docs/sessions/2025-12-20_canary_deployment_100pct_rollout.md`. |

---

## Next Actions (When User Instructs)

### Immediate (Slice 1 — VM Baseline)
1. Create Compute Engine VM in DEV (project-38-ai)
   - Machine type: e2-medium (or user preference)
   - Boot disk: Ubuntu 24.04 LTS or Debian 12
   - Network: default VPC (no custom VPC needed initially)
   - **Service Account:** `n8n-runtime@project-38-ai.iam.gserviceaccount.com`
2. Reserve and assign external static IP
3. Configure firewall rules: SSH (22), HTTP (80), HTTPS (443)
4. Install Docker + Docker Compose on VM
5. Validate secret access: n8n-runtime can read its 3 secrets (metadata check only)
   - Use impersonation: `--impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com`

**CRITICAL:** All gcloud commands MUST include `--project project-38-ai`

### Short-Term (Slice 2 — Workload Deployment)
7. Deploy N8N via Docker Compose on VM
8. Deploy Kernel service via Docker Compose
9. Configure inter-service communication (Docker network)
10. Validate secret injection into containers

### Medium-Term (Slice 3 — Testing)
11. Run smoke tests on VM
12. Validate logging (Cloud Logging integration)
13. Test end-to-end workflows
14. Document performance baseline

### Long-Term (Slice 4 — PROD Mirror)
15. Get user approval for PROD deployment
16. Replicate VM setup in PROD (project-38-ai-prod)
17. Deploy workloads to PROD VM
18. Final validation and cutover

### Optional/Deferred (Phase 2B/3 — Advanced Infrastructure)
- Migrate to Cloud SQL if managed DB needed
- Implement Cloud NAT if private networking required
- Set up custom VPC for advanced networking
- Add load balancing for horizontal scaling

---

## Evidence Links

- **Secrets:** `docs/context/secret_sync_history.md`
- **Project Facts:** `docs/context/project_facts.md`
- **Operating Rules:** `docs/context/operating_rules.md`
- **GCP Projects:** DEV=project-38-ai, PROD=project-38-ai-prod
- **Repository:** https://github.com/edri2or-commits/project-38
- **Workspace:** `<WORKSPACE_PATH>`
