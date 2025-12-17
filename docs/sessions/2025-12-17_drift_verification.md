# Session Brief — 2025-12-17 — Drift Verification & Secret Investigation

**Date:** 2025-12-17  
**Duration:** ~3 hours  
**Session Type:** Investigation + Documentation  
**GitHub Impact:** Commit 9dcd9bb (already pushed)

---

## Session Overview

**Objective:** Verify commit 9dcd9bb (drift closure), validate VM deployment state, investigate secret handling

**Outcome:** ✅ Commit validated, 🚨 Critical discovery: VM running with placeholder secrets

**Key Achievement:** Complete forensic analysis of Postgres authentication + drift reconciliation between repo (SSOT) and VM (runtime)

---

## Timeline

### Phase 1: Commit Verification (10 min)
- **Action:** Reviewed git show for commit 9dcd9bb
- **Scope:** 3 files changed (docker-compose.yml, README.md, execution_log.md)
- **Changes:** Image pinning (SHA256 digests), security hardening, WEBHOOK_URL caveat

### Phase 2: Secret Investigation (60 min)
- **Trigger:** User requested verification of secrets inside containers
- **Discovery:** All 3 secrets are backslash literals (`\`)
  - `POSTGRES_PASSWORD=\` (2 bytes: 0x5c + newline)
  - `N8N_ENCRYPTION_KEY=\` (2 bytes: 0x5c + newline)
  - `N8N_TELEGRAM_BOT_TOKEN=\` (2 bytes: 0x5c + newline)
- **Evidence:** docker inspect, printenv, wc -c, od -An -tx1

### Phase 3: Postgres Authentication Mystery (90 min)
- **Question:** How does Postgres accept connections with invalid password `\`?
- **Investigation:**
  1. N8N container IP: 172.18.0.3
  2. Postgres container IP: 172.18.0.2
  3. pg_hba.conf line 27: `host all all all scram-sha-256`
  4. User `n8n` has password: YES (not NULL)
  5. Connection test: `PGPASSWORD=\ psql -h postgres -U n8n -d n8n -c 'SELECT 1'` → SUCCESS
- **Resolution:** Password `\` is the **correct password** (set during container init), stored as SCRAM-SHA-256 hash in pg_authid

### Phase 4: Gates Validation (30 min)
- **Gate #1 - Encryption Key Risk:**
  - ✅ Verified: 0 credentials in DB (credentials_entity, shared_credentials, variables)
  - ✅ No encryption errors in logs
  - ✅ Safe to change N8N_ENCRYPTION_KEY
  
- **Gate #2 - Postgres Auth:**
  - ✅ Proven: scram-sha-256 authentication via pg_hba.conf line 27
  - ✅ Password `\` is valid (not trust mode, not passwordless)
  - ✅ Connection succeeds because backslash matches stored hash
  
- **Gate #3 - Data Loss Risk:**
  - ✅ 0 credentials to lose
  - ✅ 6 workflows (all simple webhook POCs, no credential references)
  - ✅ Safe for re-deployment with real secrets

---

## Actions Performed

### 1. Git Show Analysis
**Commands:**
```bash
git show --stat 9dcd9bb
git show 9dcd9bb -- deployment/n8n/docker-compose.yml
git show 9dcd9bb -- deployment/n8n/README.md
git show 9dcd9bb -- docs/phase-2/slice-02a_execution_log.md
```

**Files Modified (Commit 9dcd9bb):**
- `deployment/n8n/docker-compose.yml` (+10/-2)
  - Images pinned: postgres:16-alpine → postgres@sha256:a507..., n8n:latest → n8n@sha256:e3a4...
  - Security hardening added: N8N_BLOCK_ENV_ACCESS_IN_NODE, NODES_EXCLUDE, N8N_SECURE_COOKIE, etc.
- `deployment/n8n/README.md` (+8/-1)
  - Removed "Health checks configured"
  - Added WEBHOOK_URL caveat (localhost-only, no reverse proxy)
- `docs/phase-2/slice-02a_execution_log.md` (+28/-1)
  - Post-execution update documenting SSOT reconciliation

---

## Critical Findings

### 🚨 Security Issue: Placeholder Secrets in Production
**Discovery:**
- VM deployed with `docker-compose.yml` containing literal backslash (`\`) for all 3 secrets
- `load-secrets.sh` script exists but was NOT executed during latest deployment
- Containers running with placeholder values instead of real GCP secrets

**Root Cause:**
- Deployment flow: `docker compose up -d` was run directly instead of via `./load-secrets.sh`
- docker-compose.yml on VM has hardcoded `POSTGRES_PASSWORD: \` etc.

**Impact:**
- ✅ Postgres: Works (password `\` is valid, set during init, hashed as scram-sha-256)
- ⚠️ N8N encryption: Key is `\` (workflows/credentials not properly encrypted)
- ⚠️ Telegram bot: Token `\` is invalid (webhooks won't work with real Telegram API)

---

## Lessons Learned

1. **Secret Injection Must Be Mandatory:** Deployment scripts must ALWAYS use `./load-secrets.sh`
2. **Trust ≠ Passwordless:** pg_hba.conf `trust` only applies to specified addresses
3. **Docker Network ≠ Localhost:** 172.18.0.0/16 is NOT 127.0.0.1
4. **Placeholder Secrets Can Work:** Password `\` is valid (not empty, not NULL)
5. **Evidence-First Investigation Works:** RAW outputs + systematic gates prevented premature conclusions

---

## Next Steps

### Immediate (Pending Approval)
1. **Re-deploy with Real Secrets:**
   ```bash
   cd /home/edri2
   ./load-secrets.sh
   ```

2. **Validate Secret Injection:**
   ```bash
   docker exec p38-postgres printenv POSTGRES_PASSWORD | wc -c  # Should be >20
   docker exec p38-n8n printenv N8N_ENCRYPTION_KEY | wc -c      # Should be >20
   ```

---

**Session Status:** ✅ Complete (Investigation)  
**Deployment Status:** ⏸️ Pending approval (re-deploy with real secrets)  
**Documentation Status:** ✅ Committed (session brief created)

**Next Action:** Await user approval for `./load-secrets.sh` execution
