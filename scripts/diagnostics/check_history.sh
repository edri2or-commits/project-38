#!/bin/bash
echo "=== workflow_history table ==="
docker exec p38-postgres psql -U n8n -d n8n -c 'SELECT * FROM workflow_history LIMIT 10;'
