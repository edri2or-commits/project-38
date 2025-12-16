#!/bin/bash
# Project 38 V2 - Secret Fetcher
# Pulls secrets from GCP Secret Manager and creates runtime .env
# Usage: ./fetch_secrets.sh [PROJECT_ID] [ENV_NAME]
#   PROJECT_ID: GCP project (default: project-38-ai)
#   ENV_NAME: dev or prod (default: dev)

set -euo pipefail

# Configuration
PROJECT_ID="${1:-project-38-ai}"
ENV_NAME="${2:-dev}"
RUNTIME_DIR="/opt/project38/runtime"
ENV_FILE="${RUNTIME_DIR}/.env"

echo "🔐 Project 38 Secret Fetcher"
echo "   Project: ${PROJECT_ID}"
echo "   Environment: ${ENV_NAME}"
echo ""

# Validate project ID
if [[ ! "${PROJECT_ID}" =~ ^project-38-ai(-prod)?$ ]]; then
    echo "❌ Invalid PROJECT_ID: ${PROJECT_ID}"
    echo "   Valid values: project-38-ai, project-38-ai-prod"
    exit 1
fi

# Ensure runtime directory exists
mkdir -p "${RUNTIME_DIR}"

# Create temporary file
TEMP_ENV=$(mktemp)

# Fetch secrets from Secret Manager
echo "📥 Fetching secrets from Secret Manager..."

# Core N8N secrets (3 secrets)
echo "   → n8n-encryption-key"
N8N_ENCRYPTION_KEY=$(gcloud secrets versions access latest \
    --secret="n8n-encryption-key" \
    --project="${PROJECT_ID}")

echo "   → postgres-password"
POSTGRES_PASSWORD=$(gcloud secrets versions access latest \
    --secret="postgres-password" \
    --project="${PROJECT_ID}")

echo "   → telegram-bot-token"
TELEGRAM_BOT_TOKEN=$(gcloud secrets versions access latest \
    --secret="telegram-bot-token" \
    --project="${PROJECT_ID}")

# LLM API keys (3 secrets - kernel runtime)
echo "   → openai-api-key"
OPENAI_API_KEY=$(gcloud secrets versions access latest \
    --secret="openai-api-key" \
    --project="${PROJECT_ID}")

echo "   → anthropic-api-key"
ANTHROPIC_API_KEY=$(gcloud secrets versions access latest \
    --secret="anthropic-api-key" \
    --project="${PROJECT_ID}")

echo "   → gemini-api-key"
GEMINI_API_KEY=$(gcloud secrets versions access latest \
    --secret="gemini-api-key" \
    --project="${PROJECT_ID}")

# GitHub PAT (kernel runtime)
echo "   → github-pat"
GITHUB_PAT=$(gcloud secrets versions access latest \
    --secret="github-pat" \
    --project="${PROJECT_ID}")

# Write to temporary file
cat > "${TEMP_ENV}" <<EOF
# Project 38 V2 Runtime Configuration
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Project: ${PROJECT_ID}
# Environment: ${ENV_NAME}
# 
# ⚠️  DO NOT COMMIT THIS FILE
# ⚠️  This file contains sensitive credentials

# ============================================
# N8N Configuration (n8n-runtime SA)
# ============================================
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

# ============================================
# Database Configuration (n8n-runtime SA)
# ============================================
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# ============================================
# Bot Integration (n8n-runtime SA)
# ============================================
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

# ============================================
# LLM API Keys (kernel-runtime SA)
# ============================================
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}

# ============================================
# GitHub Integration (kernel-runtime SA)
# ============================================
GITHUB_PAT=${GITHUB_PAT}
EOF

# Move temp file to final location
mv "${TEMP_ENV}" "${ENV_FILE}"

# Set secure permissions (readable only by owner)
chmod 600 "${ENV_FILE}"

# Verify file was created
if [ -f "${ENV_FILE}" ]; then
    echo ""
    echo "✅ Secrets fetched successfully"
    echo "📁 Environment file: ${ENV_FILE}"
    echo "🔒 Permissions: $(stat -c '%a' ${ENV_FILE} 2>/dev/null || stat -f '%Lp' ${ENV_FILE})"
    echo "👤 Owner: $(stat -c '%U:%G' ${ENV_FILE} 2>/dev/null || stat -f '%Su:%Sg' ${ENV_FILE})"
    echo ""
    echo "⚠️  SECURITY REMINDER:"
    echo "   - Never commit ${ENV_FILE} to Git"
    echo "   - Never share ${ENV_FILE} in chat/logs"
    echo "   - Rotate secrets if exposed"
else
    echo ""
    echo "❌ Failed to create environment file"
    exit 1
fi
