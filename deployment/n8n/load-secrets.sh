#!/bin/bash
set -euo pipefail

PROJECT_ID="project-38-ai"

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Fetching secrets from GCP Secret Manager..."

# Fetch secrets (n8n-runtime SA has access to these 3 only)
export POSTGRES_PASSWORD=$(gcloud secrets versions access latest --secret=postgres-password --project=$PROJECT_ID)
export N8N_ENCRYPTION_KEY=$(gcloud secrets versions access latest --secret=n8n-encryption-key --project=$PROJECT_ID)
export TELEGRAM_BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=$PROJECT_ID)

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Secrets loaded (3/3). Starting Docker Compose..."

# Start services with secrets as environment variables
docker compose up -d

echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] Services started. Use 'docker compose ps' to check status."
