#!/bin/bash
echo "=== Recent Executions ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, \"workflowId\", status, \"startedAt\" FROM execution_entity ORDER BY \"startedAt\" DESC LIMIT 5;"

echo ""
echo "=== Dedup Test: Same update_id again ==="
curl -s -X POST 'https://count-allowing-licensing-demands.trycloudflare.com/webhook/telegram-v2' \
  -H 'Content-Type: application/json' \
  -d @/home/edri2/tg_test_payload.json

echo ""
echo ""
echo "=== Check executions after dedup test ==="
sleep 3
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, \"workflowId\", status, \"startedAt\" FROM execution_entity ORDER BY \"startedAt\" DESC LIMIT 5;"
