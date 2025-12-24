#!/bin/bash
set -e

echo "=== Import workflow ==="
docker cp /home/edri2/simple_webhook.json p38-n8n:/tmp/simple_webhook.json
docker exec p38-n8n n8n import:workflow --input=/tmp/simple_webhook.json 2>&1 || true

echo "=== List workflows ==="
docker exec p38-n8n n8n list:workflow

echo "=== Activate ALL in DB ==="
docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET active=true;"

echo "=== Restart n8n ==="
docker restart p38-n8n
sleep 20

echo "=== Check logs ==="
docker logs p38-n8n --tail 10 2>&1 | grep -i active || true

echo "=== Test webhooks ==="
echo "poc-simple:"
curl -s -w " [HTTP:%{http_code}]" http://localhost:5678/webhook/poc-simple
echo ""
echo "poc-headless-test:"
curl -s -w " [HTTP:%{http_code}]" http://localhost:5678/webhook/poc-headless-test
echo ""
