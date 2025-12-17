#!/bin/bash
set -euo pipefail

PROJECT_ID="project-38-ai"

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Fetching secrets from GCP Secret Manager..."

# Fetch secrets (n8n-runtime SA has access to these 3 only)
export POSTGRES_PASSWORD=$(gcloud secrets versions access latest --secret=postgres-password --project=$PROJECT_ID)
export N8N_ENCRYPTION_KEY=$(gcloud secrets versions access latest --secret=n8n-encryption-key --project=$PROJECT_ID)
export TELEGRAM_BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=$PROJECT_ID)

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Secrets fetched. Validating..."

# Gate 1: Non-empty check
if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$N8N_ENCRYPTION_KEY" ] || [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "ERROR: One or more secrets are empty. Aborting."
  exit 1
fi

# Gate 2: Length check (reject placeholders like single backslash)
if [ ${#POSTGRES_PASSWORD} -lt 10 ]; then
  echo "ERROR: POSTGRES_PASSWORD too short (${#POSTGRES_PASSWORD} chars). Expected >=10. Aborting."
  exit 1
fi

if [ ${#N8N_ENCRYPTION_KEY} -lt 10 ]; then
  echo "ERROR: N8N_ENCRYPTION_KEY too short (${#N8N_ENCRYPTION_KEY} chars). Expected >=10. Aborting."
  exit 1
fi

if [ ${#TELEGRAM_BOT_TOKEN} -lt 10 ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN too short (${#TELEGRAM_BOT_TOKEN} chars). Expected >=10. Aborting."
  exit 1
fi

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ✅ All secrets validated (lengths: PG=${#POSTGRES_PASSWORD}, N8N=${#N8N_ENCRYPTION_KEY}, TG=${#TELEGRAM_BOT_TOKEN})"

# Gate 3: Check if Postgres container exists and has data
if docker ps -a --format '{{.Names}}' | grep -q '^p38-postgres$'; then
  echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Postgres container exists. Checking if password rotation needed..."
  
  # Test current password (if it fails, rotation needed)
  CURRENT_PW_LENGTH=$(docker exec p38-postgres printenv POSTGRES_PASSWORD | wc -c)
  
  if [ "$CURRENT_PW_LENGTH" -eq 2 ]; then
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ⚠️  Current password is placeholder (2 bytes). Rotating password in database..."
    
    # Rotate password in Postgres
    docker exec p38-postgres psql -U n8n -d n8n -c "ALTER USER n8n PASSWORD '$POSTGRES_PASSWORD';" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
      echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ✅ Password rotated successfully in Postgres"
    else
      echo "ERROR: Failed to rotate password in Postgres. Aborting."
      exit 1
    fi
  else
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Current password length: $CURRENT_PW_LENGTH bytes (non-placeholder). Skipping rotation."
  fi
else
  echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Postgres container not found. Will be created with new password."
fi

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Starting Docker Compose with validated secrets..."

# Start services with secrets as environment variables
docker compose up -d

echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ✅ Services started. Use 'docker compose ps' to check status."
