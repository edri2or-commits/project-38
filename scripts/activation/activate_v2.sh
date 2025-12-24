#!/bin/bash
WF_NAME="Telegram POC v2"
WF_ID=$(docker exec p38-postgres psql -U n8n -d n8n -t -c "SELECT id FROM workflow_entity WHERE name='$WF_NAME';" | tr -d ' ')
VERSION_ID=$(docker exec p38-postgres psql -U n8n -d n8n -t -c "SELECT \"versionId\" FROM workflow_entity WHERE id='$WF_ID';" | tr -d ' ')

echo "ID: $WF_ID, Version: $VERSION_ID"

docker exec p38-postgres psql -U n8n -d n8n -c "
INSERT INTO workflow_history (\"versionId\", \"workflowId\", authors, \"createdAt\", \"updatedAt\", nodes, connections, name, autosaved)
SELECT '$VERSION_ID', id, '[]', NOW(), NOW(), nodes, connections, name, false FROM workflow_entity WHERE id='$WF_ID';"

docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET active=true, \"activeVersionId\"='$VERSION_ID' WHERE id='$WF_ID';"

docker restart p38-n8n
sleep 20

echo "=== Testing ==="
curl -s -X POST "http://localhost:5678/webhook/telegram-v2" -H "Content-Type: application/json" -d '{"update_id": 111111, "message": {"chat": {"id": 123}, "text": "Hello POC", "from": {"first_name": "Tester"}}}'
echo ""
echo "HTTP Code:"
curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:5678/webhook/telegram-v2" -H "Content-Type: application/json" -d '{"update_id": 222222, "message": {"chat": {"id": 123}, "text": "Second msg"}}'
