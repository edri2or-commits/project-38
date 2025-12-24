#!/bin/bash
set -e

echo "=== POC-02: Telegram Workflow Activation ==="

# 1. Import workflow
echo "[1/5] Importing workflow..."
docker cp /home/edri2/telegram_receiver.json p38-n8n:/tmp/telegram_receiver.json
docker exec p38-n8n n8n import:workflow --input=/tmp/telegram_receiver.json 2>&1

# 2. Get workflow ID
echo "[2/5] Getting workflow ID..."
sleep 2
WF_ID=$(docker exec p38-postgres psql -U n8n -d n8n -t -c "SELECT id FROM workflow_entity WHERE name='Telegram POC Receiver' LIMIT 1;" | tr -d ' ')
echo "Workflow ID: $WF_ID"

# 3. Get versionId
VERSION_ID=$(docker exec p38-postgres psql -U n8n -d n8n -t -c "SELECT \"versionId\" FROM workflow_entity WHERE id='$WF_ID';" | tr -d ' ')
echo "Version ID: $VERSION_ID"

# 4. Create history record
echo "[3/5] Creating history record..."
docker exec p38-postgres psql -U n8n -d n8n -c "
INSERT INTO workflow_history 
  (\"versionId\", \"workflowId\", authors, \"createdAt\", \"updatedAt\", nodes, connections, name, autosaved)
SELECT 
  '$VERSION_ID', id, '[]', NOW(), NOW(), nodes, connections, name, false 
FROM workflow_entity 
WHERE id='$WF_ID';"

# 5. Activate
echo "[4/5] Activating workflow..."
docker exec p38-postgres psql -U n8n -d n8n -c "
UPDATE workflow_entity 
SET active=true, \"activeVersionId\"='$VERSION_ID' 
WHERE id='$WF_ID';"

# 6. Restart
echo "[5/5] Restarting n8n..."
docker restart p38-n8n
sleep 20

# Verify
echo "=== Verification ==="
docker logs p38-n8n 2>&1 | grep -i "Activated" | tail -3
echo ""
echo "Testing webhook endpoint..."
curl -s -X POST "http://localhost:5678/webhook/telegram-bot" \
  -H "Content-Type: application/json" \
  -d '{"update_id": 999999, "message": {"chat": {"id": 123}, "text": "POC test", "from": {"first_name": "TestUser"}}}'
