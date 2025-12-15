# Slice 2A Evidence Pack — N8N Deployment

**Date:** [YYYY-MM-DD]  
**Start:** [HH:MM:SS UTC]  
**End:** [HH:MM:SS UTC]  
**Duration:** [X minutes]  
**Environment:** DEV (project-38-ai)  
**Executor:** [Claude/User]  
**Status:** 🔄 NOT STARTED

---

## Pre-Execution Checklist

**Timestamp:** [HH:MM:SS UTC]

### Prerequisites Verification

#### VM Status
```bash
# Command
gcloud compute instances list --project=project-38-ai --filter="name=p38-dev-vm-01"

# Output
[PENDING EXECUTION]

# Result
[ ] VM running
[ ] External IP matches 136.111.39.139
[ ] Service account: n8n-runtime
```

#### SSH Connectivity
```bash
# Command
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="echo 'SSH OK'"

# Output
[PENDING EXECUTION]

# Result
[ ] SSH successful
```

#### Docker Status
```bash
# Command
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="docker --version && docker compose version"

# Output
[PENDING EXECUTION]

# Result
[ ] Docker 29.1.3+
[ ] Docker Compose 5.0.0+
```

#### Secrets Metadata (3 secrets only)
```bash
# Command
gcloud secrets list --project=project-38-ai --filter="name:(n8n-encryption-key OR postgres-password OR telegram-bot-token)" --format="table(name,replication.automatic)"

# Output
[PENDING EXECUTION]

# Result
[ ] 3 secrets exist (n8n-encryption-key, postgres-password, telegram-bot-token)
[ ] All secrets have ENABLED versions
```

---

## Step 1: Create docker-compose.yml

**Timestamp:** [HH:MM:SS UTC]

### Command
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cat > /home/\$(whoami)/docker-compose.yml << 'EOF'
[COMPOSE FILE CONTENT - 2 services: postgres, n8n]
EOF"
```

### Output (RAW)
```
[PENDING EXECUTION]
```

### Verification
```bash
# Command
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="cat /home/\$(whoami)/docker-compose.yml"

# Output
[PENDING EXECUTION]
```

### Result
- [ ] ✅ SUCCESS / ❌ FAILED
- [ ] File exists at /home/user/docker-compose.yml
- [ ] Contains 2 services (postgres, n8n)
- [ ] N8N port bound to 127.0.0.1:5678 (localhost only)
- [ ] Environment variables use ${VAR} syntax

---

## Step 2: Create Secret Fetcher Script

**Timestamp:** [HH:MM:SS UTC]

### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="cat > /home/\$(whoami)/load-secrets.sh << 'EOF'
[SCRIPT CONTENT - 3 secrets only]
EOF
chmod +x /home/\$(whoami)/load-secrets.sh"
```

### Output (RAW)
```
[PENDING EXECUTION]
```

### Verification
```bash
# Command
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="ls -la /home/\$(whoami)/load-secrets.sh"

# Output
[PENDING EXECUTION]
```

### Result
- [ ] ✅ SUCCESS / ❌ FAILED
- [ ] File exists
- [ ] Executable permissions set (+x)
- [ ] Script fetches 3 secrets only (n8n-encryption-key, postgres-password, telegram-bot-token)

---

## Step 3: Run Secret Loader and Start Services

**Timestamp:** [HH:MM:SS UTC]

### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="cd /home/\$(whoami) && ./load-secrets.sh"
```

### Output (RAW)
```
[PENDING EXECUTION]

Expected:
[YYYY-MM-DD HH:MM:SS UTC] Fetching secrets from GCP Secret Manager...
[YYYY-MM-DD HH:MM:SS UTC] Secrets loaded (3/3). Starting Docker Compose...
[+] Running 4/4
 ✔ Network project38-network       Created
 ✔ Volume "postgres_data"          Created
 ✔ Volume "n8n_data"                Created
 ✔ Container p38-postgres           Started
 ✔ Container p38-n8n                Started
[YYYY-MM-DD HH:MM:SS UTC] Services started.
```

### Verification
```bash
# Command
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="docker compose ps"

# Output
[PENDING EXECUTION]
```

### Result
- [ ] ✅ SUCCESS / ❌ FAILED
- [ ] 2 containers running (postgres, n8n)
- [ ] No exit codes
- [ ] All Status: Up

---

## Step 4: Verify Service Health

**Timestamp:** [HH:MM:SS UTC]

### 4.1: Container Status

#### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker compose ps --format '{{.Name}}\t{{.State}}\t{{.Status}}'"
```

#### Output (RAW)
```
[PENDING EXECUTION]

Expected:
p38-postgres    running    Up X seconds (healthy)
p38-n8n         running    Up X seconds
```

#### Result
- [ ] All containers State: running
- [ ] postgres shows (healthy)

### 4.2: Postgres Health

#### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker exec p38-postgres pg_isready -U n8n"
```

#### Output (RAW)
```
[PENDING EXECUTION]

Expected:
/var/run/postgresql:5432 - accepting connections
```

#### Result
- [ ] ✅ Postgres accepting connections

### 4.3: N8N Health

#### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="curl -s http://localhost:5678/healthz"
```

#### Output (RAW)
```
[PENDING EXECUTION]

Expected:
{"status": "ok"}
```

#### Result
- [ ] ✅ N8N health endpoint responds

---

## Step 5: Setup SSH Port-Forward

**Timestamp:** [HH:MM:SS UTC]

### Command (Run Locally)
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  -- -L 5678:localhost:5678 -N
```

**Note:** This command runs in a separate terminal and remains open (tunnel active).

### Output (RAW)
```
[PENDING EXECUTION]

Expected:
(no output - tunnel established in background)
```

### Verification (Browser)

**URL:** http://localhost:5678/

**Result:**
- [ ] ✅ N8N UI loads
- [ ] ✅ Login/setup page visible
- [ ] Screenshot saved: [PATH]

---

## Step 6: Check Docker Logs

**Timestamp:** [HH:MM:SS UTC]

### Postgres Logs

#### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker logs p38-postgres --tail 20"
```

#### Output (RAW)
```
[PENDING EXECUTION]
```

#### Result
- [ ] No critical errors
- [ ] Database initialized

### N8N Logs

#### Command
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker logs p38-n8n --tail 20"
```

#### Output (RAW)
```
[PENDING EXECUTION]
```

#### Result
- [ ] No authentication failures
- [ ] Server started on port 5678

---

## Stop Condition Check

**Exit Criteria:**
- [X] 2 containers running (postgres, n8n)
- [X] All health checks passing
- [X] N8N UI accessible via SSH port-forward
- [X] Secrets loaded (3 only: n8n-encryption-key, postgres-password, telegram-bot-token)
- [X] No secret values exposed

**Met:** [ ] ✅ Yes / [ ] ❌ No

**Evidence Summary:**
[TO BE FILLED DURING EXECUTION]

**Blockers (if any):**
[NONE / LIST BLOCKERS]

---

## Artifacts Created

**Containers:**
- [ ] p38-postgres (postgres:16-alpine)
- [ ] p38-n8n (n8nio/n8n:latest)

**Networks:**
- [ ] project38-network (bridge)

**Volumes:**
- [ ] postgres_data
- [ ] n8n_data

**Files on VM:**
- [ ] /home/user/docker-compose.yml
- [ ] /home/user/load-secrets.sh

---

## Security Validation

### Secret Exposure Check

**Locations checked for secret values:**
- [ ] docker-compose.yml: ✅ Only ${VAR} placeholders
- [ ] load-secrets.sh: ✅ No hardcoded values
- [ ] Docker logs: ✅ No [REDACTED] values exposed
- [ ] Environment vars: ⚠️ Visible in `docker inspect Config.Env` (expected - mitigation via Docker socket access control)

**Result:** [ ] ✅ NO SECRET VALUES IN FILES/LOGS (docker inspect exposure is expected & mitigated)

### Least Privilege Validation

**n8n-runtime SA access verified:**
- [ ] ✅ Can access: n8n-encryption-key
- [ ] ✅ Can access: postgres-password
- [ ] ✅ Can access: telegram-bot-token
- [ ] ✅ Cannot access: openai-api-key (correct - not needed)
- [ ] ✅ Cannot access: anthropic-api-key (correct - not needed)
- [ ] ✅ Cannot access: gemini-api-key (correct - not needed)
- [ ] ✅ Cannot access: github-pat (correct - not needed)

**Result:** [ ] ✅ LEAST PRIVILEGE CONFIRMED

---

## Performance Metrics

**Execution Times:**
- Step 1 (docker-compose.yml): [X seconds]
- Step 2 (secret script): [X seconds]
- Step 3 (service start): [X seconds]
- Step 4 (health checks): [X seconds]
- Step 5 (port-forward setup): [X seconds]
- Step 6 (log review): [X seconds]

**Total Duration:** [X minutes Y seconds]

---

## Next Steps

**If SUCCESS:**
- [ ] Update traceability_matrix.md (Slice 2A → DONE)
- [ ] Proceed to Slice 2B/3: Kernel Deployment
  - Decision needed: Separate VM with kernel-runtime SA?
  - Architecture review required

**If FAILED:**
- [ ] Review error in execution log
- [ ] Consult rollback plan
- [ ] Execute rollback if partial deployment
- [ ] Document blocker
- [ ] Wait for user instruction

---

**End of Evidence Pack Template**

**Note:** This template will be populated during Slice 2A execution. All [PENDING EXECUTION] sections will be replaced with actual outputs.

**Scope:** Slice 2A deploys N8N only. Kernel deferred to separate slice due to SA permission boundaries (least privilege).
