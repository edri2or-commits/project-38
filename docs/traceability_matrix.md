# Traceability Matrix — Project 38 (V2)

**Last Updated:** 2025-12-21 (Stage 2A: Echo Bot via GitHub Actions)  
**Purpose:** Track completion status and evidence for all project components

---

## Legend

| Status | Meaning |
|--------|---------|
| ✅ DONE | Completed and verified with evidence |
| 🔄 IN PROGRESS | Currently being worked on |
| 📋 NEXT | Queued for execution (not started) |
| ⏸️ DEFERRED | Postponed to later phase |
| ❌ BLOCKED | Cannot proceed (dependencies not met) |

---

## Component Status Table

| Component | Status | Phase | Evidence | Notes |
|-----------|--------|-------|----------|-------|
| **Secrets (GCP Secret Manager)** | ✅ DONE | PRE-BUILD | SYNC_OK / FINAL_OK | 7 secrets × 2 projects, 2 ENABLED versions each |
| **IAM (Service Accounts)** | ✅ DONE | PRE-BUILD | IAM_OK | 3 SA per project + least privilege matrix |
| **Context Documentation** | ✅ DONE | PRE-BUILD | Files in docs/context/ | 4 canonical files created |
| **GitHub App (project-38-scribe)** | ✅ DONE | Infrastructure | [GitHub App Docs](github-app/) | Created 2025-12-18 • Actions/Contents/Workflows R/W |
| **GitHub Webhook Receiver** | ✅ DONE | Infrastructure | [Session Brief](sessions/2025-12-20_canary_deployment_100pct_rollout.md) | Cloud Run (us-central1) • Revision 00009-lfb • Command Parsing MVP (/label, /assign) • Deployed 2025-12-20 |
| **Stage 2A: Echo Bot** | ✅ DONE | IssueOps | [Evidence](evidence/2025-12-21_stage_2a_echo_bot_e2e.txt) • [Issue #24](https://github.com/edri2or-commits/project-38/issues/24#issuecomment-3679601920) | GitHub Actions workflow • Gate 2A CLOSED • E2E loop verified • Deployed 2025-12-21 |
| **Strategic Narrative (PROJECT_NARRATIVE.md)** | ✅ DONE | Phase 1 | Root file | Entry point document with "why" and "how" (2025-12-16) |
| **Deployment Scripts** | ✅ DONE | Phase 2 | Root scripts | 4 automation scripts: deployment/scripts/fetch_secrets.sh, deployment/archive/startup.sh, p38_sync_secrets.ps1, gpt_google_workspace_schema.yaml (2025-12-16, commit c70a8a1) |
| **Infrastructure (Slice 1 - VM Baseline)** | ✅ DONE | Slice 1 | [Execution Log](phase-2/slice-01_execution_log.md) | Completed 2025-12-15 • VM + Docker + IAM verified |
| **Advanced Infrastructure (Cloud SQL, NAT, VPC)** | ⏸️ OPTIONAL/DEFERRED | Phase 2B/3 | N/A | Only if scaling/managed DB required |
| **Workload Deployment (Slice 2A - N8N)** | ✅ DONE | Slice 2A | [Execution Log](phase-2/slice-02a_execution_log.md) | Completed 2025-12-16 • N8N + Postgres deployed (72 min) |
| **POC-01: Headless Activation + Hardening** | ✅ PASS | Phase 2 | [POC-01 Doc](phase-2/poc-01_headless_hardening.md) | Completed 2025-12-16 • Headless workflow activation verified |
| **POC-02: Telegram Webhook Integration** | ✅ PASS | Phase 2 | [POC-02 Doc](phase-2/poc-02_telegram_webhook.md) | Completed 2025-12-16 • Telegram webhook + dedup verified |
| **POC-03: Full Conversation Flow** | ⏸️ BLOCKED | Phase 2 | [POC-03 Issues](sessions/2025-12-17_poc03_issues.md) | Workflows imported, activation blocked (credentials + webhook registration) |
| **Workload Deployment (Slice 2B/3 - Kernel)** | ⏸️ DEFERRED | Slice 2B/3 | Pending | Kernel service - SA architecture TBD |
| **Testing & Validation (Slice 3)** | 📋 NEXT | Slice 3 | Pending | DEV environment validation |
| **PROD Mirror (Slice 4)** | ⏸️ DEFERRED | Slice 4 | Pending | After DEV approval |

---

## Detailed Status: Secrets

### Status: ✅ DONE (FINAL_OK)

**Evidence:**
- **DEV (project-38-ai):** 7 secrets, each with 2 ENABLED versions
- **PROD (project-38-ai-prod):** 7 secrets, each with 2 ENABLED versions
- **Verification:** Metadata checks performed, no values exposed
- **Documentation:** `secret_sync_history.md` contains full inventory

**Secret List:**
1. anthropic-api-key ✅
2. gemini-api-key ✅
3. github-pat ✅
4. n8n-encryption-key ✅
5. openai-api-key ✅
6. postgres-password ✅
7. telegram-bot-token ✅

**Action Required:** None — secrets are ready for use

---

## Detailed Status: IAM

### Status: ✅ DONE (IAM_OK)

**Evidence:**
- **DEV:** 3 service accounts with least privilege access ✅
- **PROD:** 3 service accounts with least privilege access ✅
- **Access Matrix:** Documented in `secret_sync_history.md`

**Service Accounts per Project:**
1. github-actions-deployer → All 7 secrets ✅
2. n8n-runtime → 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token) ✅
3. kernel-runtime → 4 secrets (LLM APIs + github-pat) + 2 project roles ✅

**kernel-runtime Additional Roles:**
- roles/logging.logWriter ✅
- roles/compute.viewer ✅

**Action Required:** None — IAM is ready for use

---

## Detailed Status: GitHub App (project-38-scribe)

### Status: ✅ DONE (Created 2025-12-18)

**Documentation:**
- [GitHub App Overview](github-app/README.md)
- [Setup Guide](github-app/setup.md)
- [Permissions Matrix](github-app/permissions.md)
- [Usage Examples](github-app/usage.md)

**App Details:**
- **Name:** project-38-scribe
- **Created:** 2025-12-18
- **Homepage:** https://github.com/edri2or-commits/project-38
- **Installed On:** edri2or-commits/project-38
- **Private Key:** `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem`

**Permissions (Repository-level):**
- ✅ Actions: Read and write
- ✅ Contents: Read and write
- ✅ Workflows: Read and write
- ✅ Metadata: Read-only (automatic)

**Webhook Configuration:**
- Status: ✅ ACTIVE (configured and verified in production)
- URL: https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook
- Features: Signature verification (HMAC-SHA256), Firestore idempotency, Fast-ACK (202), Command Parsing (/label, /assign)
- Deployment: Cloud Run (us-central1), revision github-webhook-receiver-00009-lfb (deployed 2025-12-20)
- Ref: PR #17 (Command Parsing MVP)

**Installation Scope:**
- Account: edri2or-commits only
- Repository: project-38 only
- Cannot access other repositories or organizations

**Use Cases:**
- Automated documentation updates
- Workflow management and dispatch
- CI/CD orchestration
- Release automation

**Security Features:**
- Granular permissions (Actions/Contents/Workflows only)
- Repository-scoped (isolated to project-38)
- Auditable (all actions attributed to "project-38-scribe[bot]")
- Revocable (can uninstall without affecting other tools)

**Next Steps:**
- [ ] Test App permissions (create test commit)
- [ ] Document usage patterns in automation
- [ ] Create example scripts using the App
- [ ] Set up monitoring for API rate limits

**Action Required:** None — App is ready for use in automation

---

## Detailed Status: GitHub Webhook Receiver

### Status: ✅ DONE (Command Parsing MVP Deployed 2025-12-20)

**Documentation:**
- [Deployment Session Brief](sessions/2025-12-20_canary_deployment_100pct_rollout.md)
- [SSOT Alignment Session](sessions/2025-12-20_scribe_mvp_ssot_alignment.md)

**Service Details:**
- **Platform:** Google Cloud Run (us-central1)
- **Current Revision:** github-webhook-receiver-00009-lfb
- **Traffic:** 100% to 00009-lfb (deployed 2025-12-20 17:18 UTC)
- **Service URL:** https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook
- **Build Commit:** dcb7682 (verified identical to main branch b07d1bb)

**Features Deployed:**
- ✅ GitHub webhook signature verification (HMAC-SHA256)
- ✅ Fast-ACK response (HTTP 202 within 10s)
- ✅ Firestore idempotency (24h deduplication)
- ✅ Command parsing MVP: `/label` and `/assign` commands
- ✅ Bot filtering (ignores bot-generated comments)
- ✅ GitHub API integration (labels, assignees)

**Deployment Strategy:**
- **Method:** Canary deployment (progressive rollout)
- **Phase 1:** 10% traffic (validation)
- **Phase 2:** 100% traffic (full rollout)
- **Verification:** Multi-gate validation (traffic state, error logs, real webhook test)
- **Downtime:** Zero
- **Rollback Capability:** Preserved (previous revision 00008-x56 available)

**Verification Results:**
- ✅ Traffic routing: 100% → 00009-lfb confirmed
- ✅ Error scan: Zero ERROR logs (30-minute window)
- ✅ Real webhook test: `/label bug` executed successfully
- ✅ GitHub API: Label added to issue #18
- ✅ Bot filtering: Correctly ignored bot comment
- ✅ HTTP responses: 202 Accepted (latency 0.05s - 1.4s)

**Previous Revisions:**
- 00008-x56: ACK responder only (no command parsing)
- 00009-lfb: Command parsing MVP (current)

**Rollback Procedure:**
```bash
# Immediate rollback to previous stable revision
gcloud run services update-traffic github-webhook-receiver \
  --region us-central1 --project project-38-ai \
  --to-revisions github-webhook-receiver-00008-x56=100
```

**Next Steps:**
- [ ] Monitor logs for 24h (anomaly detection)
- [ ] Expand command repertoire (additional IssueOps commands)
- [ ] Optional: Remove "canary" tag (cosmetic cleanup)

**Action Required:** None — Command parsing MVP operational in production

---

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
