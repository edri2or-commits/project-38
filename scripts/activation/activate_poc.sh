#!/bin/bash
set -e
echo "=== Activating workflow via DB ==="
docker exec p38-postgres psql -U n8n -d n8n -c "UPDATE workflow_entity SET active=true WHERE id='6fFDwVjdwDzkkFLj';"
echo "=== Restarting n8n ==="
docker restart p38-n8n
sleep 15
echo "=== Testing webhook ==="
curl -s -w "\nHTTP_CODE: %{http_code}\n" http://localhost:5678/webhook/poc-headless-test
