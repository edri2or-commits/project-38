#!/bin/bash
set -e

echo "=== Fix activeVersionId for ALL workflows ==="
docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET \"activeVersionId\" = \"versionId\" WHERE \"activeVersionId\" IS NULL;"

echo "=== Verify ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, name, active, \"activeVersionId\" FROM workflow_entity;"

echo "=== Restart n8n ==="
docker restart p38-n8n
sleep 20

echo "=== Check activation logs ==="
docker logs p38-n8n 2>&1 | grep -i "Activated" | tail -5

echo "=== Test ALL webhooks ==="
echo "poc-final:"
curl -s -w " [HTTP:%{http_code}]\n" http://localhost:5678/webhook/poc-final
echo "poc-simple:"
curl -s -w " [HTTP:%{http_code}]\n" http://localhost:5678/webhook/poc-simple
echo "poc-headless-test:"
curl -s -w " [HTTP:%{http_code}]\n" http://localhost:5678/webhook/poc-headless-test
