#!/bin/bash
echo "=== Test 1: NEW update_id (666666) ==="
cat > /tmp/new_update.json << 'EOF'
{"update_id": 666666, "message": {"message_id": 2, "chat": {"id": 12345, "type": "private"}, "text": "New message", "from": {"id": 999, "first_name": "NewTest", "is_bot": false}}}
EOF
curl -s -X POST 'https://count-allowing-licensing-demands.trycloudflare.com/webhook/telegram-v2' \
  -H 'Content-Type: application/json' \
  -d @/tmp/new_update.json
echo ""

sleep 2

echo ""
echo "=== Test 2: SAME update_id (666666) - should be dedup ==="
curl -s -X POST 'https://count-allowing-licensing-demands.trycloudflare.com/webhook/telegram-v2' \
  -H 'Content-Type: application/json' \
  -d @/tmp/new_update.json
echo ""

sleep 2

echo ""
echo "=== Executions after both tests ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, status, \"startedAt\" FROM execution_entity WHERE \"workflowId\"='fyYPOaF7uoCMsa2U' ORDER BY \"startedAt\" DESC LIMIT 4;"
