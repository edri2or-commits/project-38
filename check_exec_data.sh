#!/bin/bash
echo "=== Last 2 executions data ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, data::text FROM execution_entity WHERE \"workflowId\"='fyYPOaF7uoCMsa2U' ORDER BY \"startedAt\" DESC LIMIT 2;" 2>/dev/null | head -100
