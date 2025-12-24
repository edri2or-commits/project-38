#!/bin/bash
set -e
echo "=== IMPORT ==="
docker cp /home/edri2/simple_webhook.json p38-n8n:/tmp/simple_webhook.json
docker exec p38-n8n n8n import:workflow --input=/tmp/simple_webhook.json

echo "=== LIST ==="
docker exec p38-n8n n8n list:workflow

echo "=== ACTIVATE VIA DB ==="
docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET active=true WHERE name='POC Simple Webhook'"

echo "=== RESTART ==="
docker restart p38-n8n
sleep 20

echo "=== TEST WEBHOOK ==="
curl -s -w '\nHTTP_CODE:%{http_code}\n' http://localhost:5678/webhook/poc-simple
