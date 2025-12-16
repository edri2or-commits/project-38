#!/bin/bash
set -e

# Create correct workflow (responseMode=onReceived = immediate response, no Respond node needed)
cat > /tmp/clean_webhook.json << 'WFJSON'
{
  "name": "POC Clean Webhook",
  "active": false,
  "versionId": "v1-clean",
  "nodes": [
    {
      "parameters": {
        "path": "poc-clean",
        "httpMethod": "GET",
        "responseMode": "onReceived",
        "responseData": "allEntries",
        "options": {}
      },
      "id": "clean-wh",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "webhookId": "poc-clean"
    }
  ],
  "connections": {},
  "settings": {
    "executionOrder": "v1"
  }
}
WFJSON

echo "=== Import workflow ==="
docker cp /tmp/clean_webhook.json p38-n8n:/tmp/clean_webhook.json
docker exec p38-n8n n8n import:workflow --input=/tmp/clean_webhook.json 2>&1

echo "=== Get new workflow ID ==="
NEW_ID=$(docker exec p38-n8n n8n list:workflow 2>&1 | grep "POC Clean" | cut -d'|' -f1)
echo "New ID: $NEW_ID"

echo "=== Create history record manually ==="
docker exec p38-postgres psql -U n8n -d n8n -c "INSERT INTO workflow_history (\"versionId\", \"workflowId\", authors, \"createdAt\", \"updatedAt\", nodes, connections, name, autosaved) SELECT 'v1-clean', id, '[]', NOW(), NOW(), nodes, connections, name, false FROM workflow_entity WHERE name='POC Clean Webhook';"

echo "=== Set active + activeVersionId ==="
docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET active=true, \"activeVersionId\"='v1-clean' WHERE name='POC Clean Webhook';"

echo "=== Verify DB ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, name, active, \"activeVersionId\" FROM workflow_entity WHERE name='POC Clean Webhook';"

echo "=== Restart n8n ==="
docker restart p38-n8n
sleep 20

echo "=== Check activation ==="
docker logs p38-n8n 2>&1 | grep -i "Activated" | tail -5

echo "=== FINAL TEST ==="
echo "Response:"
curl -s http://localhost:5678/webhook/poc-clean
echo ""
echo "HTTP Code:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/webhook/poc-clean
