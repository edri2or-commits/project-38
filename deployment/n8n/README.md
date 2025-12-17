# N8N Local Deployment

**Environment:** Local development (Windows)  
**Status:** ✅ Operational  
**Last Updated:** 2025-12-17

---

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- `C:\Users\edri2\p38-n8n.env` file with secrets (see Setup section)

### Start Services
```bash
cd C:\Users\edri2\project_38\deployment\n8n
docker compose --env-file C:\Users\edri2\p38-n8n.env up -d
```

### Access n8n
Open browser: http://localhost:5678

### Stop Services
```bash
docker compose --env-file C:\Users\edri2\p38-n8n.env down
# Note: Does NOT delete volumes (data persists)
```

---

## Setup

### 1. Environment File

**Location:** `C:\Users\edri2\p38-n8n.env` (OUTSIDE repository)

**Required variables:**
```bash
POSTGRES_PASSWORD=<from-gcp-secret-manager>
N8N_ENCRYPTION_KEY=<from-gcp-secret-manager>
TELEGRAM_BOT_TOKEN=<from-gcp-secret-manager>
```

**Create from GCP Secret Manager:**
```powershell
# Fetch secrets
$pg = gcloud secrets versions access latest --secret=postgres-password --project=project-38-ai
$n8n = gcloud secrets versions access latest --secret=n8n-encryption-key --project=project-38-ai
$tg = gcloud secrets versions access latest --secret=telegram-bot-token --project=project-38-ai

# Create env file
@"
POSTGRES_PASSWORD=$pg
N8N_ENCRYPTION_KEY=$n8n
TELEGRAM_BOT_TOKEN=$tg
"@ | Out-File -FilePath C:\Users\edri2\p38-n8n.env -Encoding ASCII
```

**⚠️ Security:**
- ✅ File is OUTSIDE repository
- ✅ Never commit to Git
- ✅ Sourced from production secrets

---

## Architecture

### Services

**n8n (Workflow Engine)**
- Image: `n8nio/n8n@sha256:e3a4256...` (version 2.0.2)
- Container: `p38-n8n`
- Port: `127.0.0.1:5678` (localhost only)
- Volume: `p38-n8n_n8n_data` → `/home/node/.n8n`

**PostgreSQL (Database)**
- Image: `postgres@sha256:a507448...` (version 16.11)
- Container: `p38-postgres`
- Port: `5432` (internal only)
- Volume: `p38-n8n_postgres_data` → `/var/lib/postgresql/data`
- Database: `n8n`
- User: `n8n`

### Network
- Name: `p38-n8n_project38-network`
- Type: Bridge
- Isolation: Internal communication only

### Volumes (Persistent Data)
```bash
docker volume ls | grep p38-n8n
p38-n8n_n8n_data         # n8n workflows, credentials, settings
p38-n8n_postgres_data    # PostgreSQL database files
```

---

## Compose File Details

**File:** `docker-compose.yml`

**Key Configuration:**
```yaml
name: p38-n8n  # Fixed project name (deterministic)

services:
  postgres:
    image: postgres@sha256:...  # Pinned for stability
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From env file
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  n8n:
    image: n8nio/n8n@sha256:...  # Pinned for stability
    depends_on:
      - postgres
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}  # From env file
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}  # From env file
    ports:
      - "127.0.0.1:5678:5678"  # Localhost only
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped
```

**Design Decisions:**
- ✅ Deterministic naming: `name: p38-n8n` prevents drift
- ✅ Pinned images: SHA256 hashes for reproducibility
- ✅ Localhost binding: Security (no external access)
- ✅ No `version:` field: Modern Compose standard
- ✅ Restart policy: Auto-recovery on failure

---

## Common Operations

### View Logs
```bash
# All services
docker compose --env-file C:\Users\edri2\p38-n8n.env logs -f

# Specific service
docker compose --env-file C:\Users\edri2\p38-n8n.env logs -f n8n
docker compose --env-file C:\Users\edri2\p38-n8n.env logs -f postgres
```

### Check Status
```bash
docker compose --env-file C:\Users\edri2\p38-n8n.env ps
```

### Restart Services
```bash
docker compose --env-file C:\Users\edri2\p38-n8n.env restart
```

### Update Images
```bash
# Pull latest (respects pinned SHA256)
docker compose --env-file C:\Users\edri2\p38-n8n.env pull

# Recreate containers
docker compose --env-file C:\Users\edri2\p38-n8n.env up -d
```

### Access PostgreSQL
```bash
docker exec -it p38-postgres psql -U n8n -d n8n
```

---

## Troubleshooting

### Issue: Postgres restart loop
**Symptoms:**
```bash
docker compose ps
# Shows: p38-postgres   Restarting (1) XX seconds ago
```

**Diagnosis:**
```bash
docker logs p38-postgres --tail 50
# Look for: "Error: Database is uninitialized and superuser password is not specified"
```

**Cause:** `POSTGRES_PASSWORD` not set or empty

**Fix:**
1. Verify env file exists: `Test-Path C:\Users\edri2\p38-n8n.env`
2. Check env file has `POSTGRES_PASSWORD=<non-empty-value>`
3. Restart with env file: `docker compose --env-file ... up -d`

**Verification:**
```bash
# Check password length (should be >2)
docker exec p38-postgres printenv POSTGRES_PASSWORD | Measure-Object -Character

# Check logs for success
docker logs p38-postgres --tail 20
# Should see: "database system is ready to accept connections"
```

### Issue: n8n cannot connect to database
**Symptoms:**
- n8n container running but workflows fail
- Error logs mention database connection

**Diagnosis:**
```bash
docker compose logs n8n | Select-String -Pattern "database|postgres"
```

**Possible causes:**
1. Postgres container not running
2. Wrong DB credentials
3. Network issue

**Fix:**
```bash
# Ensure postgres is up first
docker compose ps postgres

# Restart both services in correct order
docker compose down
docker compose --env-file C:\Users\edri2\p38-n8n.env up -d
```

### Issue: Warning about unset variables
**Symptoms:**
```
level=warning msg="The POSTGRES_PASSWORD variable is not set. Defaulting to a blank string."
```

**Cause:** Running `docker compose` command WITHOUT `--env-file` flag

**Fix:** Always include `--env-file C:\Users\edri2\p38-n8n.env`

---

## Security

### Port Binding
- ✅ n8n bound to `127.0.0.1:5678` (localhost only)
- ✅ Postgres internal only (no external port)
- ✅ No services exposed to network

### Secrets Management
- ✅ Secrets in external file (not in repo)
- ✅ Sourced from GCP Secret Manager
- ✅ File permissions: User-only access
- ❌ Do NOT commit `C:\Users\edri2\p38-n8n.env` to Git

### Data Encryption
- ✅ n8n encrypts credentials with `N8N_ENCRYPTION_KEY`
- ⚠️ Key must remain stable (changing = data loss)
- ✅ Key stored in GCP Secret Manager

---

## Data Persistence

### Volumes
Data persists across container restarts:
- **n8n workflows:** Stored in `p38-n8n_n8n_data`
- **Postgres data:** Stored in `p38-n8n_postgres_data`

### Backup (Manual)
```bash
# Export n8n workflows
docker exec p38-n8n n8n export:workflow --all --output=/tmp/workflows.json
docker cp p38-n8n:/tmp/workflows.json ./backup/

# Backup Postgres
docker exec p38-postgres pg_dump -U n8n n8n > ./backup/db_backup.sql
```

### Restore (Manual)
```bash
# Import n8n workflows
docker cp ./backup/workflows.json p38-n8n:/tmp/
docker exec p38-n8n n8n import:workflow --input=/tmp/workflows.json

# Restore Postgres
docker exec -i p38-postgres psql -U n8n -d n8n < ./backup/db_backup.sql
```

### Complete Reset (⚠️ DATA LOSS)
```bash
# Stop and remove containers + volumes
docker compose --env-file C:\Users\edri2\p38-n8n.env down -v

# Restart fresh
docker compose --env-file C:\Users\edri2\p38-n8n.env up -d
```

---

## References

### Documentation
- **Docker Compose:** https://docs.docker.com/compose/
- **Compose env files:** https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/
- **n8n Documentation:** https://docs.n8n.io/
- **n8n Docker:** https://docs.n8n.io/hosting/installation/docker/
- **Postgres Image:** https://hub.docker.com/_/postgres

### Session Logs
- **Setup session:** [docs/sessions/2025-12-17_local_secret_fix.md](../../docs/sessions/2025-12-17_local_secret_fix.md)
- **Determinism fix:** [docs/sessions/2025-12-17_determinism_stabilization.md](../../docs/sessions/2025-12-17_determinism_stabilization.md)

### GCP Resources
- **Project:** `project-38-ai`
- **Secrets:**
  - `postgres-password`
  - `n8n-encryption-key`
  - `telegram-bot-token`

---

## Support

**Issues or questions?**
1. Check logs: `docker compose logs -f`
2. Verify status: `docker compose ps`
3. Review session logs: `docs/sessions/`
4. Consult troubleshooting section above

**Environment healthy when:**
- ✅ Both containers show `Up` status
- ✅ n8n accessible at http://localhost:5678
- ✅ No restart loops in `docker compose ps`
- ✅ Logs show "ready to accept connections" (postgres)
- ✅ No warnings about unset variables