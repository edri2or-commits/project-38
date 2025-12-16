# N8N Deployment Files

**Purpose:** Docker Compose configuration for N8N workflow engine + PostgreSQL database

**Target:** DEV VM (p38-dev-vm-01)

**Created:** 2025-12-16

---

## Files

### docker-compose.yml
Defines 2 services:
- **postgres**: PostgreSQL 16 Alpine (database for N8N)
- **n8n**: N8N workflow engine (latest)

**Key Features:**
- Port 5678 bound to localhost only (127.0.0.1)
- Secrets passed as environment variables
- Persistent volumes for data
- Health checks configured
- Bridge network for inter-service communication

### load-secrets.sh
Runtime secret fetcher from GCP Secret Manager.

**Secrets Fetched:**
1. n8n-encryption-key
2. postgres-password
3. telegram-bot-token

**Usage:**
```bash
cd /home/edri2
./load-secrets.sh
```

**Security:**
- Fetches secrets at runtime (not stored in files)
- Exports as environment variables for Docker Compose
- Uses latest secret versions
- No values exposed in logs

---

## Deployment Instructions

### Prerequisites
- ✅ VM: p38-dev-vm-01 running
- ✅ Docker + Docker Compose installed on VM
- ✅ Service Account: n8n-runtime attached to VM
- ✅ Secrets: 3 secrets in GCP Secret Manager with IAM access

### Steps

1. **Copy files to VM:**
```powershell
gcloud compute scp docker-compose.yml p38-dev-vm-01:/home/edri2/ --zone=us-central1-a --project=project-38-ai
gcloud compute scp load-secrets.sh p38-dev-vm-01:/home/edri2/ --zone=us-central1-a --project=project-38-ai
```

2. **Make script executable:**
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="chmod +x /home/edri2/load-secrets.sh"
```

3. **Deploy services:**
```bash
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai --command="cd /home/edri2 && ./load-secrets.sh"
```

4. **Establish SSH port-forward:**
```powershell
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai -- -L 5678:localhost:5678 -N
```

5. **Access N8N UI:**
```
http://localhost:5678
```

---

## Verification

### Container Status
```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Expected output:
```
NAME           IMAGE                STATUS              PORTS
p38-n8n        n8nio/n8n:latest     Up X minutes        127.0.0.1:5678->5678/tcp
p38-postgres   postgres:16-alpine   Up X minutes        5432/tcp
```

### Health Checks
```bash
# Postgres
docker exec p38-postgres pg_isready -U n8n_user

# N8N API
curl -s http://localhost:5678/healthz
```

Expected: Both return success

---

## Rollback

```bash
# Stop and remove containers
docker compose down

# Remove volumes (if needed)
docker volume rm edri2_postgres_data edri2_n8n_data

# Remove network
docker network rm edri2_project38-network

# Remove files
rm /home/edri2/docker-compose.yml /home/edri2/load-secrets.sh
```

---

## Evidence

See full execution log: [docs/phase-2/slice-02a_execution_log.md](../../docs/phase-2/slice-02a_execution_log.md)

**Execution Date:** 2025-12-16  
**Duration:** ~72 minutes  
**Result:** ✅ SUCCESS