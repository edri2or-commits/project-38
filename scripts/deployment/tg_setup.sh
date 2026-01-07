#!/bin/bash
TUNNEL_URL="https://count-allowing-licensing-demands.trycloudflare.com"
WEBHOOK_URL="${TUNNEL_URL}/webhook/telegram-v2"

BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=project-38-ai)

echo "=== Delete existing ==="
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"
echo ""

echo "=== Set webhook ==="
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"${WEBHOOK_URL}\"}"
echo ""

echo "=== Verify ==="
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
echo ""
