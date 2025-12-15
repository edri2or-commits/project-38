# Slice 2A Runbook — N8N Deployment (DEV)

**Version:** 2.0 (Revised - Least Privilege)  
**Date:** 2025-12-15  
**Phase:** PRE-BUILD → Execution Planning  
**Environment:** DEV only (project-38-ai)  
**Status:** 📋 PLANNING (Not yet executed)

---

## Executive Summary

**Goal:** Deploy N8N workflow engine with Postgres database on DEV VM using Docker Compose

**Scope:** Slice 2A focuses on N8N only. Kernel deployment deferred to Slice 2B/3 pending SA architecture decision.

**Approach:** 
- Use existing VM from Slice 1 (p38-dev-vm-01)
- Deploy via Docker Compose (2 services: Postgres + N8N)
- Secrets injected at runtime via GCP Secret Manager API (NO secret values in files)
- **Least Privilege:** Only 3 secrets accessible by n8n-runtime SA
- **Networking:** Access N8N via SSH port-forward (not direct :5678)

**Prerequisites:**
- ✅ Slice 1 complete (VM + Docker + IAM verified)
- ✅ n8n-runtime SA configured with access to 3 secrets only
- ✅ VM has internet access (external IP)

**Duration Estimate:** 20-30 minutes

---

## Prerequisites Verification

### Required Resources (Must Exist from Slice 1)

| Resource | Name/ID | Status Check |
|----------|---------|--------------|
| VM | p38-dev-vm-01 | `gcloud compute instances list --project=project-38-ai` |
| Static IP | p38-dev-ip-01 (136.111.39.139) | `gcloud compute addresses list --project=project-38-ai` |
| Docker | 29.1.3+ | SSH + `docker --version` |
| Docker Compose | 5.0.0+ | SSH + `docker compose version` |
| Service Account | n8n-runtime@project-38-ai.iam.gserviceaccount.com | VM metadata |

### Required Secrets (Must Exist - Read Metadata Only)

| Secret | Used By | Verification |
|--------|---------|--------------|
| n8n-encryption-key | N8N | `gcloud secrets versions list n8n-encryption-key --project=project-38-ai` |
| postgres-password | N8N (DB) | `gcloud secrets versions list postgres-password --project=project-38-ai` |
| telegram-bot-token | N8N (webhook) | `gcloud secrets versions list telegram-bot-token --project=project-38-ai` |

**Note:** Only verify secret existence (metadata), never access values during planning.

**Least Privilege Validation:** n8n-runtime SA has access to ONLY these 3 secrets (verified in Slice 1).

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────┐
│  p38-dev-vm-01 (e2-medium)             │
│  Service Account: n8n-runtime           │
│  Secrets: 3 only (n8n, postgres, tg)   │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │  Docker Compose Network         │  │
│  │                                  │  │
│  │  ┌──────────┐    ┌───────────┐ │  │
│  │  │ N8N      │◄───┤ Postgres  │ │  │
│  │  │ :5678    │    │ :5432     │ │  │
│  │  └──────────┘    └───────────┘ │  │
│  │                                  │  │
│  └─────────────────────────────────┘  │
│                                         │
│  Access: SSH port-forward only         │
│  Secrets: GCP Secret Manager API       │
└─────────────────────────────────────────┘
```

### Services

**1. PostgreSQL (Database)**
- Image: `postgres:16-alpine`
- Port: 5432 (internal only)
- Data: Docker volume `postgres_data`
- Credentials: From `postgres-password` secret

**2. N8N (Workflow Engine)**
- Image: `n8nio/n8n:latest`
- Port: 5678 (internal only, accessed via SSH port-forward)
- Database: PostgreSQL
- Secrets:
  - `n8n-encryption-key` (DB encryption)
  - `postgres-password` (DB connection)
  - `telegram-bot-token` (webhook integration)

### Network

**Docker Bridge Network:** `project38-network`
- Services communicate via service names (e.g., `postgres:5432`)
- N8N port 5678 NOT exposed externally
- Access via SSH port-forward: `localhost:5678 → VM:5678`

**Firewall:** Current rules (22/80/443) unchanged. Port 5678 not opened.

---

## Step-by-Step Execution Plan

### Step 0: Pre-Execution Checklist

**Before starting, verify:**
- [ ] Slice 1 execution log reviewed (VM/Docker/IAM confirmed)
- [ ] SSH access to VM working
- [ ] gcloud authenticated as correct user
- [ ] Current working directory: `C:\Users\edri2\project_38`

**Commands to run locally:**
```bash
# Verify gcloud auth
gcloud auth list

# Verify VM status
gcloud compute instances list --project=project-38-ai

# Test SSH
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="echo 'SSH OK'"
```

### Step 0.5: CRITICAL Preflight Check - gcloud on VM

**Objective:** Verify gcloud CLI is installed on VM (required for secret fetching)

**Why:** The `load-secrets.sh` script uses `gcloud secrets versions access` to fetch secrets from GCP Secret Manager. If gcloud is not installed, secret loading will fail.

**Verification Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="which gcloud"
```

**Expected Output if gcloud EXISTS:**
```
/usr/bin/gcloud
```
(or similar path like `/snap/bin/gcloud`, `/usr/local/bin/gcloud`)

**If gcloud NOT FOUND:**
```
(no output or "command not found" error)
```

---

#### Plan A: Install google-cloud-cli (Recommended)

**If gcloud not found, install Google Cloud SDK:**

```bash
# Install gcloud on VM
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="
sudo apt-get update && \
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl && \
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
echo 'deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main' | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
sudo apt-get update && \
sudo apt-get install -y google-cloud-sdk
"
```

**Verification after install:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="gcloud --version"
```

**Expected Output:**
```
Google Cloud SDK [version]
...
```

**Duration:** ~2-3 minutes

---

#### Plan B: Secret Manager API via Metadata Token (Alternative)

**If gcloud install fails or is not preferred, use GCP Metadata Service + Secret Manager API directly:**

**Modified load-secrets.sh script (without gcloud):**
```bash
#!/bin/bash
set -euo pipefail

PROJECT_ID="project-38-ai"

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Fetching project number from metadata service..."

# Get PROJECT_NUMBER from VM metadata (no gcloud needed)
PROJECT_NUMBER=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id")

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Fetching access token from metadata service..."

# Get access token from VM metadata service
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Fetching secrets from Secret Manager API..."

# Fetch secrets via REST API
# Note: Secret Manager returns payload.data (Base64 encoded), not plaintext
export POSTGRES_PASSWORD=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://secretmanager.googleapis.com/v1/projects/$PROJECT_NUMBER/secrets/postgres-password/versions/latest:access" | \
  grep -o '"data":"[^"]*' | cut -d'"' -f4 | base64 -d)

export N8N_ENCRYPTION_KEY=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://secretmanager.googleapis.com/v1/projects/$PROJECT_NUMBER/secrets/n8n-encryption-key/versions/latest:access" | \
  grep -o '"data":"[^"]*' | cut -d'"' -f4 | base64 -d)

export TELEGRAM_BOT_TOKEN=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://secretmanager.googleapis.com/v1/projects/$PROJECT_NUMBER/secrets/telegram-bot-token/versions/latest:access" | \
  grep -o '"data":"[^"]*' | cut -d'"' -f4 | base64 -d)

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Secrets loaded (3/3). Starting Docker Compose..."

docker compose up -d

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Services started."
```

**Note:** This approach requires NO gcloud - all data fetched from VM metadata service. Secret Manager API returns `payload.data` (Base64 encoded), not `plaintext`.

**Pros of Plan B:**
- No additional package installation
- Uses VM's built-in metadata service
- IAM permissions still enforced (n8n-runtime SA)

**Cons of Plan B:**
- More complex script
- Less readable than gcloud commands
- Base64 decoding required

---

#### Recommendation

**Use Plan A (gcloud install) unless:**
- Installation fails repeatedly
- VM has restricted package manager access
- Security policy forbids additional CLI tools

**Decision:** To be made at execution time based on preflight check result.

---

---

### Step 1: Create docker-compose.yml on VM

**Objective:** Create Docker Compose configuration on VM with secret placeholders

**Method:** Use heredoc to create file via SSH (avoids local file upload)

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cat > /home/\$(whoami)/docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: p38-postgres
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - project38-network
    restart: unless-stopped

  n8n:
    image: n8nio/n8n:latest
    container_name: p38-n8n
    ports:
      - \"127.0.0.1:5678:5678\"
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: \${POSTGRES_PASSWORD}
      N8N_ENCRYPTION_KEY: \${N8N_ENCRYPTION_KEY}
      WEBHOOK_URL: http://136.111.39.139/
      N8N_TELEGRAM_BOT_TOKEN: \${TELEGRAM_BOT_TOKEN}
    depends_on:
      - postgres
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - project38-network
    restart: unless-stopped

volumes:
  postgres_data:
  n8n_data:

networks:
  project38-network:
    driver: bridge
EOF"
```

**Expected Output:**
```
(no output - success)
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cat /home/\$(whoami)/docker-compose.yml"
```

**Success Criteria:**
- File exists on VM
- Contains 2 services (postgres, n8n)
- N8N port bound to 127.0.0.1 (localhost only)
- Environment variables use \${VAR} placeholder syntax

**Key Changes from Original Plan:**
- ❌ Removed Kernel service (deferred to Slice 2B/3)
- ✅ N8N port bound to localhost only (127.0.0.1:5678:5678)
- ✅ Only 3 secrets referenced

---

### Step 2: Create Secret Fetcher Script

**Objective:** Create bash script to fetch secrets from GCP Secret Manager and set as environment variables

**Why:** Docker Compose cannot directly access GCP secrets; we need a wrapper script

**Important:** Script fetches ONLY 3 secrets (n8n-runtime SA has access to these only)

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cat > /home/\$(whoami)/load-secrets.sh << 'EOF'
#!/bin/bash
set -euo pipefail

PROJECT_ID=\"project-38-ai\"

echo \"[\$(date -u +\"%Y-%m-%d %H:%M:%S UTC\")] Fetching secrets from GCP Secret Manager...\"

# Fetch secrets (n8n-runtime SA has access to these 3 only)
export POSTGRES_PASSWORD=\$(gcloud secrets versions access latest --secret=postgres-password --project=\$PROJECT_ID)
export N8N_ENCRYPTION_KEY=\$(gcloud secrets versions access latest --secret=n8n-encryption-key --project=\$PROJECT_ID)
export TELEGRAM_BOT_TOKEN=\$(gcloud secrets versions access latest --secret=telegram-bot-token --project=\$PROJECT_ID)

echo \"[\$(date -u +\"%Y-%m-%d %H:%M:%S UTC\")] Secrets loaded (3/3). Starting Docker Compose...\"

# Start services with secrets as environment variables
docker compose up -d

echo \"[\$(date -u +\"%Y-%m-%d %H:%M:%S UTC\")] Services started. Use 'docker compose ps' to check status.\"
EOF
chmod +x /home/\$(whoami)/load-secrets.sh"
```

**Expected Output:**
```
(no output - success)
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="ls -la /home/\$(whoami)/load-secrets.sh"
```

**Success Criteria:**
- File `load-secrets.sh` exists
- File is executable (chmod +x)
- Script fetches 3 secrets only (n8n-encryption-key, postgres-password, telegram-bot-token)
- Script exports them as environment variables
- Script starts Docker Compose

**Key Changes from Original Plan:**
- ❌ Removed 4 Kernel secrets (openai, anthropic, gemini, github-pat)
- ✅ Only 3 secrets fetched (least privilege)

---

### Step 3: Run Secret Loader and Start Services

**Objective:** Execute secret fetcher script to load secrets and start Docker Compose stack

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cd /home/\$(whoami) && ./load-secrets.sh"
```

**Expected Output:**
```
[2025-12-15 HH:MM:SS UTC] Fetching secrets from GCP Secret Manager...
[2025-12-15 HH:MM:SS UTC] Secrets loaded (3/3). Starting Docker Compose...
[+] Running 4/4
 ✔ Network project38-network       Created
 ✔ Volume "postgres_data"          Created
 ✔ Volume "n8n_data"                Created
 ✔ Container p38-postgres           Started
 ✔ Container p38-n8n                Started
[2025-12-15 HH:MM:SS UTC] Services started. Use 'docker compose ps' to check status.
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker compose ps"
```

**Success Criteria:**
- 2 containers running (Status: Up)
- No exit codes
- Postgres healthy
- N8N accessible on port 5678 (localhost only)

**Key Changes from Original Plan:**
- ✅ Only 2 containers (postgres, n8n)
- ❌ No kernel container

---

### Step 4: Verify Service Health

**Objective:** Confirm all services are healthy and accessible

#### 4.1: Check Container Status

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker compose ps --format '{{.Name}}\t{{.State}}\t{{.Status}}'"
```

**Expected Output:**
```
p38-postgres    running    Up X seconds (healthy)
p38-n8n         running    Up X seconds
```

**Note:** Removed jq dependency - using Docker's built-in format template instead.

#### 4.2: Check Postgres Health

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker exec p38-postgres pg_isready -U n8n"
```

**Expected Output:**
```
/var/run/postgresql:5432 - accepting connections
```

#### 4.3: Check N8N Health

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="curl -s http://localhost:5678/healthz"
```

**Expected Output:**
```json
{"status": "ok"}
```

**Success Criteria:**
- All 2 containers running
- Postgres accepting connections
- N8N health endpoint responds

**Key Changes from Original Plan:**
- ❌ No kernel health check (service removed)
- ✅ Simplified container status output (no jq)

---

### Step 5: Setup SSH Port-Forward for N8N Access

**Objective:** Create SSH tunnel to access N8N UI from local machine

**Why:** Firewall only allows 22/80/443. Port 5678 not exposed. SSH port-forward is secure and minimal.

**Command (Run Locally - Leave Open):**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  -- -L 5678:localhost:5678 -N
```

**Explanation:**
- `-L 5678:localhost:5678`: Forward local port 5678 → VM localhost:5678
- `-N`: No remote command (just tunnel)
- Leave this command running in a terminal

**Expected Output:**
```
(no output - tunnel established)
```

**Verification:**
Open browser on local machine:
```
http://localhost:5678
```

**Expected:** N8N login/setup page loads

**Success Criteria:**
- SSH tunnel established
- N8N UI accessible via http://localhost:5678
- No firewall changes needed

**To Stop Tunnel:**
Press `Ctrl+C` in the terminal running the SSH command.

**Key Changes from Original Plan:**
- ✅ SSH port-forward replaces direct :5678 access
- ✅ No firewall rule changes needed
- ✅ Secure access (SSH encrypted tunnel)

---

### Step 6: Check Docker Logs (Sanity Check)

**Objective:** Review container logs for errors

#### Postgres Logs
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker logs p38-postgres --tail 20"
```

#### N8N Logs
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker logs p38-n8n --tail 20"
```

**Success Criteria:**
- No critical errors
- No authentication failures
- Services initialized successfully

**Key Changes from Original Plan:**
- ❌ No kernel logs (service removed)

---

## Stop Conditions

**Proceed with execution ONLY IF:**
- ✅ Slice 1 complete (VM + Docker verified)
- ✅ User provides explicit instruction to execute Slice 2A
- ✅ No blocking issues found during prerequisite verification

**STOP execution if:**
- ❌ VM not accessible
- ❌ Docker not working
- ❌ Secret access fails (IAM issue)
- ❌ Any step returns unexpected error

**In case of STOP:**
1. Document the blocker in execution log
2. Do NOT proceed to next step
3. Consult rollback plan if partial deployment occurred
4. Report status to user and wait for instruction

---

## Expected Outcomes

**After successful execution:**
1. ✅ Docker Compose stack running on p38-dev-vm-01
2. ✅ 2 containers running (postgres, n8n)
3. ✅ All health checks passing
4. ✅ Secrets injected at runtime (no values in files)
5. ✅ N8N UI accessible via SSH port-forward (localhost:5678)
6. ✅ Secrets injected as ENV vars (visible in `docker inspect` - mitigation: restrict Docker socket access)

**Evidence Required:**
- Container status output (docker compose ps)
- Health check responses
- Screenshot of N8N UI loading via port-forward
- Port-forward command running in terminal

**Next Steps:**
- Slice 2B/3: Kernel Deployment
  - Decision needed: Separate VM with kernel-runtime SA? Or different approach?
  - Deferred until SA architecture finalized
- Slice 3: Testing & Validation
  - Create test N8N workflow
  - Test secret rotation
  - Validate logging

---

## Notes

### Security
- Secrets NEVER stored in files (only in GCP Secret Manager)
- Secrets loaded at runtime via `load-secrets.sh`
- **Note:** ENV vars visible in `docker inspect` - mitigation: restrict Docker socket access (no `docker` group membership for untrusted users)
- Service account permissions validated (n8n-runtime: 3 secrets only)
- SSH port-forward for secure access (no exposed ports)

### Networking
- N8N port 5678 bound to localhost only (127.0.0.1)
- Access via SSH port-forward (encrypted tunnel)
- Postgres port 5432 internal only
- No firewall changes needed

### Data Persistence
- PostgreSQL data: Docker volume `postgres_data`
- N8N data: Docker volume `n8n_data`
- Volumes survive container restarts

### Kernel Deferred (Slice 2B/3)
**Why:** Kernel requires 4 additional secrets (openai, anthropic, gemini, github-pat) which n8n-runtime SA does not have access to.

**Options for Slice 2B/3:**
1. **Separate VM** with kernel-runtime SA (preferred - cleaner isolation)
2. ~~**Multi-SA on same VM**~~ (NOT SUPPORTED: GCE allows only 1 SA per VM)
3. **Credential file** approach (less preferred - violates least-privilege principle)

**Decision:** Separate VM recommended for Kernel (cleanest SA isolation).

### Future Enhancements (Not in Slice 2A)
- ⏸️ HTTPS/TLS via reverse proxy on port 80/443 (Slice 3 or later)
- ⏸️ Cloud SQL migration (optional, Phase 2B)
- ⏸️ Load balancing (optional, scaling phase)
- ⏸️ Monitoring/alerting (Slice 3)

---

**End of Runbook**
