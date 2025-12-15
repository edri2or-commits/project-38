# Phase 2 Slices — Baseline Deployment Plan

**Execution Mode**: Sequential (each slice blocks next)  
**Status**: Planning only — NO builds/deploys until explicit approval  
**Workspace**: `C:\Users\edri2\project_38`

---

## Execution Rules

1. **Documentation First**: Every slice must be documented in markdown BEFORE execution
2. **Verification Required**: Stop condition must pass before proceeding to next slice
3. **No Rollback = No Deploy**: Slice 7 (rollback test) blocks production traffic
4. **Manual Approval Gates**: Slices 1, 4, 6, 9 require explicit "proceed" confirmation

---

## Slice 1: Deployment Baseline

### Goal
Reproducible VM setup from scratch with Docker runtime ready

### Inputs
- GCP project ID: `[TBD]`
- SSH public key
- Region: `us-central1-a` (per V1 proven zone)
- VM spec: `e2-medium` (4GB RAM, 2 vCPU)

### Outputs
- VM instance running (name: `project38-vm`)
- Docker + Docker Compose installed (versions: Docker 24.x, Compose 2.x)
- Firewall rules created:
  - `22/tcp` (SSH)
  - `80/tcp` (HTTP, for Let's Encrypt challenge)
  - `443/tcp` (HTTPS)
- Static external IP assigned and documented

### Steps (Planning Checklist)
```bash
# 1. Create VM with startup script
gcloud compute instances create project38-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-ssd \
  --metadata-from-file=startup-script=startup.sh \
  --tags=http-server,https-server

# 2. Reserve static IP
gcloud compute addresses create project38-ip --region=us-central1

# 3. Assign static IP to VM
gcloud compute instances add-access-config project38-vm \
  --access-config-name="External NAT" \
  --address=[RESERVED_IP]

# 4. Create firewall rules
gcloud compute firewall-rules create allow-http \
  --target-tags=http-server --allow=tcp:80
gcloud compute firewall-rules create allow-https \
  --target-tags=https-server --allow=tcp:443
```

### Verify
```bash
# VM is running
gcloud compute instances describe project38-vm \
  --zone=us-central1-a \
  --format="get(status)"
# Expected: RUNNING

# Docker installed
ssh project38-vm "docker --version"
# Expected: Docker version 24.x.x

# Compose installed
ssh project38-vm "docker compose version"
# Expected: Docker Compose version 2.x.x

# Firewall allows HTTPS
curl -I http://[STATIC_IP]
# Expected: Connection established (even if 404)
```

### Stop Condition
✅ Can SSH into VM  
✅ `docker ps` works without sudo  
✅ Static IP documented in `docs/infrastructure/vm_details.md`

---

## Slice 2: Secret Manager Setup (CORE Secrets Only)

### Goal
Zero secrets in Git or local files; all CORE credentials in GCP Secret Manager

### Scope: CORE Secrets ONLY
**Included** (baseline deployment requirements):
- `n8n-encryption-key` (n8n database encryption)
- `n8n-admin-password` (UI login)
- `postgres-password` (database)
- `telegram-bot-token` (webhook integration)
- `openai-api-key` OR `anthropic-api-key` (LLM provider)

**DEFERRED** (integration pack, non-baseline):
- Make.com API key
- Zapier credentials
- Notion integration token
- Google OAuth client secrets
- GitHub PAT
- Slack bot tokens

### Inputs
- GCP project ID
- Service account for VM (auto-created or specify: `project38-vm@[PROJECT].iam.gserviceaccount.com`)
- Secret values (provided via secure channel, not in Git)

### Outputs
- 5 secrets created in Secret Manager (namespace: `project38/*`)
- IAM binding: VM service account has `roles/secretmanager.secretAccessor`
- Script: `fetch_secrets.sh` (pulls secrets → writes `.env` on VM)
- `.env.template` file in Git (structure only, no values)

### Steps (Planning Checklist)
```bash
# 1. Create secrets (manual, one-time)
echo -n "SECRET_VALUE" | gcloud secrets create project38/n8n-encryption-key \
  --data-file=- --replication-policy=automatic

# Repeat for all 5 CORE secrets

# 2. Grant VM access
gcloud secrets add-iam-policy-binding project38/n8n-encryption-key \
  --member="serviceAccount:project38-vm@[PROJECT].iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Deploy fetch script to VM
scp fetch_secrets.sh project38-vm:/opt/project38/
ssh project38-vm "chmod +x /opt/project38/fetch_secrets.sh"
```

### fetch_secrets.sh (Pseudocode)
```bash
#!/bin/bash
# Pulls CORE secrets from Secret Manager → writes .env

set -euo pipefail

SECRETS=(
  "n8n-encryption-key"
  "n8n-admin-password"
  "postgres-password"
  "telegram-bot-token"
  "openai-api-key"
)

ENV_FILE="/opt/project38/.env"
> "$ENV_FILE"  # Truncate

for secret in "${SECRETS[@]}"; do
  value=$(gcloud secrets versions access latest \
    --secret="project38/${secret}" --format='get(payload.data)' | base64 -d)
  
  # Convert to ENV var format (e.g., n8n-encryption-key → N8N_ENCRYPTION_KEY)
  var_name=$(echo "$secret" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
  echo "${var_name}=${value}" >> "$ENV_FILE"
done

chmod 600 "$ENV_FILE"
echo "✅ Secrets fetched: $(wc -l < "$ENV_FILE") variables"
```

### Verify
```bash
# On VM:
ssh project38-vm "/opt/project38/fetch_secrets.sh"

# Check .env exists with all secrets
ssh project38-vm "cat /opt/project38/.env | grep -E '(N8N_ENCRYPTION_KEY|TELEGRAM_BOT_TOKEN|OPENAI_API_KEY)' | wc -l"
# Expected: 5 (all CORE secrets present)

# Verify no empty values
ssh project38-vm "grep '=$' /opt/project38/.env"
# Expected: No output (no empty values)
```

### Stop Condition
✅ All 5 CORE secrets in Secret Manager  
✅ `.env` file generated on VM with no manual input  
✅ No secrets committed to Git (only `.env.template`)


---

## Slice 3: Docker Compose + Caddy HTTPS

### Goal
Reverse proxy serving HTTPS with auto-provisioned Let's Encrypt certificate

### Inputs
- `docker-compose.yml` (defines: caddy, n8n, postgres, redis, litellm)
- Domain name (e.g., `project38.example.com`) pointed to static IP
- `.env` file from Slice 2

### Outputs
- 5 containers running: caddy, n8n, postgres, redis, litellm
- Caddy auto-provisions Let's Encrypt cert (no manual cert management)
- HTTPS endpoint active: `https://project38.example.com/healthz`

### docker-compose.yml (Simplified Structure)
```yaml
version: '3.8'

services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    restart: always

  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_ADMIN_PASSWORD}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      # Webhook URL must match Caddy proxy
      - WEBHOOK_URL=https://project38.example.com
    volumes:
      - n8n_data:/home/node/.n8n
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  litellm:
    image: ghcr.io/berriai/litellm:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: always

volumes:
  caddy_data:
  caddy_config:
  n8n_data:
  postgres_data:
```

### Caddyfile (Reverse Proxy Config)
```
project38.example.com {
  reverse_proxy n8n:5678
  
  # Health check endpoint
  handle /healthz {
    respond "OK" 200
  }
}
```

### Steps (Planning Checklist)
```bash
# 1. Copy files to VM
scp docker-compose.yml project38-vm:/opt/project38/
scp Caddyfile project38-vm:/opt/project38/

# 2. Start containers
ssh project38-vm "cd /opt/project38 && docker compose up -d"

# 3. Wait for Caddy to provision cert (30-60s)
sleep 60

# 4. Verify HTTPS
curl -I https://project38.example.com/healthz
```

### Verify
```bash
# All containers UP
ssh project38-vm "docker ps --format 'table {{.Names}}\t{{.Status}}'"
# Expected: 5 containers with "Up" status

# Caddy provisioned cert
ssh project38-vm "docker logs project38-caddy 2>&1 | grep 'certificate obtained'"
# Expected: Success message

# HTTPS works
curl -f https://project38.example.com/healthz
# Expected: HTTP 200, body "OK"

# No cert warnings
curl --insecure https://project38.example.com/healthz 2>&1 | grep -i "certificate"
# Expected: Valid certificate (no warnings)
```

### Stop Condition
✅ HTTPS endpoint responds with valid Let's Encrypt cert  
✅ No manual cert installation required  
✅ Caddy auto-renews cert (verified in logs: renewal job scheduled)


---

## Slice 4: n8n Hello World Workflow

### Goal
Prove n8n can execute workflows and respond to webhooks programmatically

### Inputs
- Simple workflow JSON (Webhook trigger → Set variable → Respond)
- n8n instance from Slice 3 (running + accessible)

### Outputs
- Workflow imported via CLI or API (not manual UI)
- Workflow **activated** with fallback handling (see below)
- Webhook returns "Hello Project 38" on POST request

### Workflow JSON (hello-world.json)
```json
{
  "name": "Hello World",
  "nodes": [
    {
      "parameters": {
        "path": "hello",
        "responseMode": "onReceived",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "webhookId": "project38-hello"
    },
    {
      "parameters": {
        "respondWith": "text",
        "responseBody": "Hello Project 38"
      },
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [450, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Respond", "type": "main", "index": 0}]]
    }
  },
  "active": true
}
```

### Activation Strategy (WITH FALLBACK)

**Primary Method: API Activation**
```bash
# Import workflow
WORKFLOW_ID=$(curl -X POST https://project38.example.com/api/v1/workflows \
  -H "Content-Type: application/json" \
  -u "admin:${N8N_ADMIN_PASSWORD}" \
  -d @hello-world.json | jq -r '.id')

# Activate via API
curl -X PATCH https://project38.example.com/api/v1/workflows/${WORKFLOW_ID} \
  -H "Content-Type: application/json" \
  -u "admin:${N8N_ADMIN_PASSWORD}" \
  -d '{"active": true}'

# CRITICAL: Verify production webhook registration
curl -X GET https://project38.example.com/api/v1/workflows/${WORKFLOW_ID} \
  -u "admin:${N8N_ADMIN_PASSWORD}" | jq '.nodes[] | select(.type == "n8n-nodes-base.webhook") | .webhookId'
# Expected: "project38-hello"
```

**Fallback Method: Manual UI Activation (Temporary Exception)**

If API activation does NOT register production webhook (webhookId missing or test-only):

```
KNOWN ISSUE: n8n CLI/API may activate workflow but fail to register production webhook listener.

FALLBACK PROCEDURE (temporary, document for Phase 3 automation):
1. Navigate to n8n UI: https://project38.example.com
2. Login with admin credentials
3. Open "Hello World" workflow
4. Click "Active" toggle (webhook icon should turn green)
5. Verify production webhook: Settings → Webhook URLs → shows /webhook/hello

VERIFICATION (same as primary method):
  curl -X POST https://project38.example.com/webhook/hello
  # Expected: "Hello Project 38" (200 OK)

EXCEPTION TRACKING:
- Document in docs/incidents/activation_fallback.md
- Set reminder: Re-test API activation after n8n version upgrade
- Target: Remove manual activation by Phase 3 (if n8n fixes API)
```

### Steps (Planning Checklist)
```bash
# 1. Copy workflow to VM
scp hello-world.json project38-vm:/opt/project38/

# 2. Attempt API import + activation
ssh project38-vm "cd /opt/project38 && ./import_workflow.sh hello-world.json"

# 3. Verify webhook registration
ssh project38-vm "curl -u admin:PASSWORD https://project38.example.com/api/v1/workflows/[ID] | jq '.nodes[] | select(.type == \"webhook\") | .webhookId'"

# 4. IF webhookId missing → Execute fallback (manual UI activation)
# 5. Test production webhook
curl -X POST https://project38.example.com/webhook/hello
```

### Verify
```bash
# Workflow exists and is active
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/workflows | \
  jq '.data[] | select(.name == "Hello World") | {id, name, active}'
# Expected: {"id": "...", "name": "Hello World", "active": true}

# Production webhook responds
curl -X POST https://project38.example.com/webhook/hello
# Expected: HTTP 200, body "Hello Project 38"

# Check execution log
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/executions?workflowId=[ID]&limit=1 | \
  jq '.data[0] | {status, mode}'
# Expected: {"status": "success", "mode": "webhook"}
```

### Stop Condition
✅ Workflow activated (via API OR manual UI with exception documented)  
✅ Webhook accessible at `/webhook/hello` (not test webhook URL)  
✅ Returns "Hello Project 38" within 500ms

**BLOCKER**: If production webhook does NOT work after both methods → STOP and escalate (do not proceed to Slice 5)

---

## Slice 5: Credential Injection (n8n)

### Goal
Workflows read credentials from environment variables (no manual UI import)

### Inputs
- Test credential (HTTP Basic Auth for external API test)
- n8n environment variables configured with credential data

### Outputs
- Credential created programmatically (not via UI)
- Workflow uses credential (HTTP Request node with auth)
- No "Credential not found" errors in execution log

### Credential Strategy

**Option A: Environment Variable Credentials** (Preferred)
```yaml
# In docker-compose.yml, add to n8n service:
environment:
  # Generic HTTP Auth credential
  - N8N_CREDENTIALS_HTTP_BASIC_AUTH={"name":"test-http-auth","type":"httpBasicAuth","data":{"user":"testuser","password":"testpass"}}
```

**Option B: API-Based Credential Creation**
```bash
# Create credential via API
curl -X POST https://project38.example.com/api/v1/credentials \
  -H "Content-Type: application/json" \
  -u "admin:${N8N_ADMIN_PASSWORD}" \
  -d '{
    "name": "test-http-auth",
    "type": "httpBasicAuth",
    "data": {
      "user": "testuser",
      "password": "testpass"
    }
  }'
```

### Test Workflow (test-credential.json)
```json
{
  "name": "Test Credential",
  "nodes": [
    {
      "parameters": {
        "path": "test-auth",
        "responseMode": "onReceived"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://httpbin.org/basic-auth/testuser/testpass",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpBasicAuth"
      },
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [450, 300],
      "credentials": {
        "httpBasicAuth": {
          "name": "test-http-auth"
        }
      }
    },
    {
      "parameters": {
        "respondWith": "allEntries"
      },
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
    "HTTP Request": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
  },
  "active": true
}
```

### Activation (Same Fallback as Slice 4)
```bash
# 1. Import workflow (API or CLI)
# 2. Activate via API
# 3. IF webhook not registered → Manual UI activation (document exception)
# 4. Verify production webhook endpoint
```

### Steps (Planning Checklist)
```bash
# 1. Add credential to .env or create via API
# 2. Restart n8n to load env-based credentials
ssh project38-vm "cd /opt/project38 && docker compose restart n8n"

# 3. Verify credential exists
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/credentials | \
  jq '.data[] | select(.name == "test-http-auth")'

# 4. Import + activate workflow (with fallback handling)
# 5. Test webhook
curl -X POST https://project38.example.com/webhook/test-auth
```

### Verify
```bash
# Credential exists (not manually imported)
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/credentials | \
  jq '.data[] | select(.name == "test-http-auth") | .name'
# Expected: "test-http-auth"

# Workflow execution succeeds with credential
curl -X POST https://project38.example.com/webhook/test-auth
# Expected: HTTP 200, body contains {"authenticated": true, "user": "testuser"}

# Check execution log for credential usage
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/executions?limit=1 | \
  jq '.data[0] | {status, error}'
# Expected: {"status": "success", "error": null}
```

### Stop Condition
✅ Credential created without UI interaction  
✅ Workflow executes with credential successfully  
✅ No "Credential not found" errors in logs  

**EXCEPTION TRACKING**: If credential must be manually imported via UI → document in `docs/incidents/credential_fallback.md`


---

## Slice 6: Telegram Bot Integration

### Goal
End-to-end Telegram message flow (send message → bot responds)

### Inputs
- Telegram bot token (from Slice 2: `TELEGRAM_BOT_TOKEN`)
- Webhook URL: `https://project38.example.com/webhook/telegram`

### Outputs
- Telegram webhook registered with Telegram servers
- n8n workflow: Telegram Trigger → Echo message
- Bot responds to `/start` command within 3s

### Workflow (telegram-echo.json)
```json
{
  "name": "Telegram Echo Bot",
  "nodes": [
    {
      "parameters": {
        "updates": ["message"]
      },
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1,
      "position": [250, 300],
      "credentials": {
        "telegramApi": {
          "name": "telegram-bot"
        }
      },
      "webhookId": "telegram-webhook"
    },
    {
      "parameters": {
        "chatId": "={{$json.message.chat.id}}",
        "text": "You said: {{$json.message.text}}"
      },
      "name": "Send Reply",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1,
      "position": [450, 300],
      "credentials": {
        "telegramApi": {
          "name": "telegram-bot"
        }
      }
    }
  ],
  "connections": {
    "Telegram Trigger": {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]}
  },
  "active": true
}
```

### Telegram Credential Setup
```bash
# Option 1: API-based credential creation
curl -X POST https://project38.example.com/api/v1/credentials \
  -u "admin:${N8N_ADMIN_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "telegram-bot",
    "type": "telegramApi",
    "data": {
      "accessToken": "'${TELEGRAM_BOT_TOKEN}'"
    }
  }'

# Option 2: Environment variable (add to docker-compose.yml)
N8N_CREDENTIALS_TELEGRAM_API='{"name":"telegram-bot","type":"telegramApi","data":{"accessToken":"'${TELEGRAM_BOT_TOKEN}'"}}'
```

### Webhook Registration with Telegram
```bash
# After workflow activation, n8n should auto-register webhook
# Verify manually:
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
# Expected: {"url": "https://project38.example.com/webhook/telegram", "pending_update_count": 0}

# If not auto-registered, manual registration:
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://project38.example.com/webhook/telegram"
```

### Steps (Planning Checklist)
```bash
# 1. Create Telegram credential (API or env var)
# 2. Import telegram-echo.json workflow
# 3. Activate workflow (with fallback handling from Slice 4)
# 4. Verify webhook registered with Telegram
# 5. Test: Send message to bot via Telegram app
```

### Verify
```bash
# Telegram credential exists
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/credentials | \
  jq '.data[] | select(.type == "telegramApi") | .name'
# Expected: "telegram-bot"

# Webhook registered with Telegram
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq '.result.url'
# Expected: "https://project38.example.com/webhook/telegram"

# Bot responds to message
# Manual test: Open Telegram, send "/start" to bot
# Expected: Bot replies "You said: /start" within 3s

# Check n8n execution log
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/executions?workflowId=[TELEGRAM_WORKFLOW_ID]&limit=1 | \
  jq '.data[0] | {status, mode}'
# Expected: {"status": "success", "mode": "webhook"}
```

### Stop Condition
✅ Telegram webhook registered (verified via Telegram API)  
✅ Bot responds to `/start` within 3s  
✅ Execution log shows successful webhook trigger

**BLOCKER**: If bot does not respond after 3 attempts → STOP (potential SSL cert or webhook URL issue)

---

## Slice 7: Rollback Test

### Goal
Prove we can undo bad deployments and restore service quickly

### Inputs
- Current working deployment (Slices 1-6 completed)
- Intentionally broken configuration (invalid env var)

### Outputs
- Rollback script (`rollback.sh`) created and tested
- Health check detects failure
- Rollback completes in <30s
- Service restored to working state

### Rollback Strategy
```
Version Management:
/opt/project38/
├── versions/
│   ├── v1/
│   │   ├── docker-compose.yml
│   │   └── .env
│   ├── v2/
│   │   ├── docker-compose.yml
│   │   └── .env
│   └── v3/
│       ├── docker-compose.yml
│       └── .env
├── current -> versions/v3 (symlink)
└── rollback.sh
```

### rollback.sh (Pseudocode)
```bash
#!/bin/bash
# Rollback to previous version

set -euo pipefail

CURRENT_LINK="/opt/project38/current"
VERSIONS_DIR="/opt/project38/versions"

# Get current version number
CURRENT_VERSION=$(readlink "$CURRENT_LINK" | grep -oP 'v\K[0-9]+')
PREVIOUS_VERSION=$((CURRENT_VERSION - 1))

if [ $PREVIOUS_VERSION -lt 1 ]; then
  echo "❌ No previous version to rollback to"
  exit 1
fi

PREVIOUS_DIR="${VERSIONS_DIR}/v${PREVIOUS_VERSION}"

if [ ! -d "$PREVIOUS_DIR" ]; then
  echo "❌ Previous version directory not found: $PREVIOUS_DIR"
  exit 1
fi

echo "🔄 Rolling back from v${CURRENT_VERSION} to v${PREVIOUS_VERSION}..."

# Stop current containers
cd "$CURRENT_LINK"
docker compose down

# Switch symlink to previous version
ln -sfn "$PREVIOUS_DIR" "$CURRENT_LINK"

# Start previous version
cd "$CURRENT_LINK"
docker compose up -d

# Wait for health check
sleep 10

# Verify health
HEALTH=$(curl -f -s https://project38.example.com/healthz || echo "FAILED")
if [ "$HEALTH" == "OK" ]; then
  echo "✅ Rollback successful to v${PREVIOUS_VERSION}"
else
  echo "❌ Rollback failed, health check returned: $HEALTH"
  exit 1
fi
```

### Test Procedure
```bash
# 1. Capture current working state as v1
ssh project38-vm "mkdir -p /opt/project38/versions/v1"
ssh project38-vm "cp /opt/project38/docker-compose.yml /opt/project38/versions/v1/"
ssh project38-vm "cp /opt/project38/.env /opt/project38/versions/v1/"
ssh project38-vm "ln -s /opt/project38/versions/v1 /opt/project38/current"

# 2. Deploy broken version (v2)
ssh project38-vm "mkdir -p /opt/project38/versions/v2"
ssh project38-vm "cp /opt/project38/versions/v1/* /opt/project38/versions/v2/"
# Break .env (invalid postgres password)
ssh project38-vm "echo 'POSTGRES_PASSWORD=INVALID_BROKEN_VALUE' >> /opt/project38/versions/v2/.env"
ssh project38-vm "ln -sfn /opt/project38/versions/v2 /opt/project38/current"
ssh project38-vm "cd /opt/project38/current && docker compose up -d"

# 3. Wait for failure
sleep 30

# 4. Health check should fail
ssh project38-vm "curl -f https://project38.example.com/healthz"
# Expected: curl exits with non-zero (connection failure or 500)

# 5. Execute rollback
ssh project38-vm "/opt/project38/rollback.sh"

# 6. Verify restoration
ssh project38-vm "curl -f https://project38.example.com/healthz"
# Expected: HTTP 200, body "OK"
```

### Verify
```bash
# Rollback script exists and is executable
ssh project38-vm "test -x /opt/project38/rollback.sh && echo 'EXISTS'"
# Expected: EXISTS

# Version directories exist
ssh project38-vm "ls -la /opt/project38/versions/"
# Expected: v1/ v2/ (at least)

# Current symlink points to working version
ssh project38-vm "readlink /opt/project38/current"
# Expected: /opt/project38/versions/v1 (after rollback)

# Service is healthy
curl -f https://project38.example.com/healthz
# Expected: HTTP 200

# Telegram bot still works (end-to-end test)
# Send message to bot → verify response
```

### Stop Condition
✅ Rollback script executes successfully  
✅ Health check passes within 30s of rollback  
✅ Telegram bot responds (proving full stack restored)

**CRITICAL**: Do NOT proceed to Slice 8 if rollback fails — this is a production safety gate


---

## Slice 8: Observability (Langfuse Integration)

### Goal
AI execution traces visible in Langfuse cloud dashboard

### Inputs
- Langfuse API keys (public + secret, added to Secret Manager)
- litellm container configured from Slice 3

### Outputs
- litellm environment variables configured with Langfuse endpoint
- Test n8n workflow with AI step (calls litellm)
- Trace visible in Langfuse UI within 10s
- litellm container status: HEALTHY (not UNHEALTHY like V1)

### litellm Configuration (docker-compose.yml update)
```yaml
litellm:
  image: ghcr.io/berriai/litellm:latest
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    # Langfuse integration
    - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
    - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
    - LANGFUSE_HOST=https://cloud.langfuse.com
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: always
```

### Test Workflow (ai-trace-test.json)
```json
{
  "name": "AI Trace Test",
  "nodes": [
    {
      "parameters": {
        "path": "ai-test",
        "responseMode": "onReceived"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "http://litellm:4000/v1/chat/completions",
        "method": "POST",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "{\n  \"model\": \"gpt-3.5-turbo\",\n  \"messages\": [{\"role\": \"user\", \"content\": \"Say 'Hello from Project 38'\"}],\n  \"metadata\": {\"trace_id\": \"{{$execution.id}}\"}\n}"
      },
      "name": "Call LLM",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [450, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{$json}}"
      },
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "Call LLM", "type": "main", "index": 0}]]},
    "Call LLM": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
  },
  "active": true
}
```

### Steps (Planning Checklist)
```bash
# 1. Add Langfuse keys to Secret Manager (2 new secrets)
gcloud secrets create project38/langfuse-public-key --data-file=-
gcloud secrets create project38/langfuse-secret-key --data-file=-

# 2. Update fetch_secrets.sh to include Langfuse keys
# 3. Update docker-compose.yml with Langfuse env vars
# 4. Restart litellm container
ssh project38-vm "cd /opt/project38 && docker compose restart litellm"

# 5. Verify litellm health
ssh project38-vm "docker ps | grep litellm"
# Expected: Status = healthy (not UNHEALTHY)

# 6. Import + activate AI test workflow
# 7. Trigger workflow
curl -X POST https://project38.example.com/webhook/ai-test

# 8. Check Langfuse UI for trace (manual verification)
```

### Verify
```bash
# litellm container is HEALTHY
ssh project38-vm "docker inspect project38-litellm | jq '.[0].State.Health.Status'"
# Expected: "healthy"

# AI workflow executes successfully
curl -X POST https://project38.example.com/webhook/ai-test
# Expected: HTTP 200, JSON response with LLM output

# Check n8n execution log
curl -u "admin:${N8N_ADMIN_PASSWORD}" \
  https://project38.example.com/api/v1/executions?limit=1 | \
  jq '.data[0] | {status, error}'
# Expected: {"status": "success", "error": null}

# Langfuse trace exists (manual UI check)
# Login to https://cloud.langfuse.com
# Search for trace_id matching n8n execution ID
# Expected: Trace visible with model=gpt-3.5-turbo, input/output logged
```

### Stop Condition
✅ litellm container shows HEALTHY status (fixes V1 issue)  
✅ 3 consecutive AI calls produce Langfuse traces  
✅ Traces include execution_id from n8n

**BLOCKER**: If litellm remains UNHEALTHY after restart → STOP and debug (check logs for auth errors)

---

## Slice 9: Monitoring + Alerts

### Goal
Detect service failures without SSH access; alerts sent automatically

### Inputs
- GCP Monitoring workspace (auto-created with project)
- Health check endpoint: `https://project38.example.com/healthz`
- Alert notification channel (email or Telegram)

### Outputs
- Uptime check monitoring health endpoint (interval: 1 minute)
- Alert policy: Fires if DOWN for >3 consecutive checks
- Test alert: Verified by stopping n8n container
- Dashboard: CPU/Memory metrics for all containers

### GCP Uptime Check Configuration
```bash
# Create uptime check (planning command, do not execute yet)
gcloud monitoring uptime-checks create https \
  --display-name="Project 38 Health" \
  --resource-type=uptime-url \
  --monitored-resource-type=uptime_url \
  --host=project38.example.com \
  --path=/healthz \
  --check-interval=60s \
  --timeout=10s
```

### Alert Policy (YAML definition for documentation)
```yaml
displayName: "Project 38 Service Down"
conditions:
  - displayName: "Health check failing"
    conditionThreshold:
      filter: |
        resource.type = "uptime_url"
        metric.type = "monitoring.googleapis.com/uptime_check/check_passed"
      comparison: COMPARISON_LT
      thresholdValue: 1
      duration: 180s  # 3 minutes
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_FRACTION_TRUE
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[EMAIL_CHANNEL_ID]
alertStrategy:
  autoClose: 1800s  # Auto-close after 30 min if recovered
```

### Notification Channel Setup
```bash
# Create email notification channel
gcloud alpha monitoring channels create \
  --display-name="Project 38 Alerts" \
  --type=email \
  --channel-labels=email_address=ops@example.com
```

### Dashboard (Metrics to Track)
```
Container CPU Usage:
  - n8n, postgres, redis, litellm, caddy
  - Alert if any >80% for 5 minutes

Container Memory Usage:
  - Alert if any >90% of limit

Disk Usage:
  - Alert if VM disk >85% full

Network Egress:
  - Track for cost anomaly detection
```

### Test Procedure
```bash
# 1. Stop n8n container (simulate failure)
ssh project38-vm "docker stop project38-n8n"

# 2. Wait 3 minutes (uptime check interval × 3)
sleep 180

# 3. Verify alert received (check email or Telegram)
# Expected: Alert notification with "Project 38 Service Down"

# 4. Restart n8n
ssh project38-vm "docker start project38-n8n"

# 5. Wait 2 minutes
sleep 120

# 6. Verify alert cleared (auto-close notification)
# Expected: "Project 38 Service Recovered" email
```

### Verify
```bash
# Uptime check exists
gcloud monitoring uptime-checks list | grep "Project 38"
# Expected: 1 uptime check listed

# Alert policy exists
gcloud alpha monitoring policies list | grep "Service Down"
# Expected: 1 alert policy listed

# Notification channel configured
gcloud alpha monitoring channels list | grep "Project 38"
# Expected: 1 notification channel (email or Telegram)

# Test alert fired (manual verification)
# Check email inbox or Telegram for alert message

# Dashboard accessible
# Navigate to GCP Console → Monitoring → Dashboards → [Project 38 Dashboard]
# Expected: Metrics visible for all 5 containers
```

### Stop Condition
✅ Uptime check monitors health endpoint  
✅ Alert fires within 3 min of service failure  
✅ Alert clears automatically when service recovers  
✅ Dashboard shows real-time container metrics

**APPROVAL GATE**: Slice 9 completion marks Phase 2 baseline COMPLETE. Requires explicit sign-off before production traffic.

---

## Execution Checklist (Pre-Flight)

Before executing ANY slice:

- [ ] Slice documented in markdown (this file)
- [ ] Inputs identified and available
- [ ] Verification commands tested (syntax checked)
- [ ] Stop condition clearly defined
- [ ] Rollback procedure documented (if applicable)
- [ ] Approval received (for Slices 1, 4, 6, 9)

---

## Risk Registry

| Slice | Risk | Mitigation |
|-------|------|------------|
| 1 | VM creation fails (quota/billing) | Verify GCP quotas + billing enabled BEFORE execution |
| 2 | Secret Manager IAM misconfigured | Test with dummy secret first |
| 3 | Let's Encrypt rate limit hit | Use staging cert for testing, production only once |
| 4 | n8n activation flaky | Fallback to manual UI activation (temporary exception) |
| 5 | Credential import requires UI | Document as known limitation + workaround |
| 6 | Telegram webhook not registered | Manual setWebhook API call |
| 7 | Rollback fails (symlink broken) | Keep direct path backup in v0/ |
| 8 | Langfuse API rate limit | Implement local trace buffer (redis queue) |
| 9 | Alert spam (false positives) | Tune threshold: 3 min DOWN before alert |

---

## Phase 2 Success Criteria

ALL of the following must be TRUE before declaring Phase 2 complete:

1. ✅ All 9 slices executed successfully (stop conditions met)
2. ✅ Zero manual credential imports (all via env vars or API)
3. ✅ Rollback tested and <30s recovery time
4. ✅ Telegram bot responds <3s (end-to-end flow working)
5. ✅ Monitoring alerts fire and auto-clear
6. ✅ No UNHEALTHY containers (all 5 services UP)
7. ✅ Incident documentation: Any manual workarounds logged in `docs/incidents/`

---

## Post-Phase 2 Actions (Planning Only)

**DEFERRED to Phase 3**:
- Integration pack secrets (Make, Zapier, Notion, Google OAuth)
- Personal agent workflows (requires Google OAuth setup)
- Context API integration (AIOS V1 component, not baseline)
- Multi-user support (authentication + authorization)
- Backup + disaster recovery procedures
- Load testing (Telegram webhook under 100 msg/s)

**Next Milestone**: Phase 3 kickoff requires:
- 7 days of stable Phase 2 operations (incident-free)
- Observability data review (Langfuse traces, GCP metrics)
- Retrospective on activation fallback (can we eliminate manual UI?)

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-15  
**Status**: Planning complete — awaiting execution approval
