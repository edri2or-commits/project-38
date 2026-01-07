#!/bin/bash
echo "=== Static Data (dedup state) ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT \"staticData\" FROM workflow_entity WHERE id='fyYPOaF7uoCMsa2U';"
