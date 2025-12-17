#!/bin/bash
# Set Telegram webhook without exposing token in logs

TUNNEL_URL="https://count-allowing-licensing-demands.trycloudflare.com"
WEBHOOK_PATH="/webhook/telegram-v2"
WEBHOOK_URL="${TUNNEL_URL}${WEBHOOK_PATH}"

echo "=== Telegram Webhook Setup ==="
echo "Webhook URL: $WEBHOOK_URL"

# Get token from Secret Manager (value not logged)
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=project-38-ai 2>/dev/null)

if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: Could not fetch bot token"
    exit 1
fi

echo "Token fetched: [REDACTED - ${#BOT_TOKEN} chars]"

# Delete existing webhook first
echo ""
echo "=== Deleting existing webhook ==="
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook" | jq .

# Set new webhook
echo ""
echo "=== Setting webhook ==="
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${WEBHOOK_URL}\"}" | jq .

# Verify
echo ""
echo "=== getWebhookInfo ==="
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq .
