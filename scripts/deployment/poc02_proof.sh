#!/bin/bash
echo "=========================================="
echo "POC-02 FINAL PROOF - $(date -u)"
echo "=========================================="

echo ""
echo "=== 1. TUNNEL URL ==="
cat /home/edri2/tunnel.log | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1

echo ""
echo "=== 2. getWebhookInfo ==="
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=project-38-ai)
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

echo ""
echo ""
echo "=== 3. Workflow Status ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, name, active FROM workflow_entity WHERE name LIKE 'Telegram%';"

echo ""
echo "=== 4. Recent Executions (Telegram workflow) ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, status, \"startedAt\" FROM execution_entity WHERE \"workflowId\"='fyYPOaF7uoCMsa2U' ORDER BY \"startedAt\" DESC LIMIT 5;"

echo ""
echo "=== 5. Live Test ==="
cat > /tmp/final_test.json << 'EOF'
{"update_id": 777777, "message": {"message_id": 99, "chat": {"id": 12345, "type": "private"}, "text": "Final POC test", "from": {"id": 999, "first_name": "FinalTest", "is_bot": false}}}
EOF
echo "Sending test update..."
curl -s -X POST 'https://count-allowing-licensing-demands.trycloudflare.com/webhook/telegram-v2' \
  -H 'Content-Type: application/json' \
  -d @/tmp/final_test.json

echo ""
echo ""
echo "=== 6. Verify Execution Created ==="
sleep 2
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, status, \"startedAt\" FROM execution_entity WHERE \"workflowId\"='fyYPOaF7uoCMsa2U' ORDER BY \"startedAt\" DESC LIMIT 1;"

echo ""
echo "=========================================="
echo "POC-02 PROOF COMPLETE"
echo "=========================================="
