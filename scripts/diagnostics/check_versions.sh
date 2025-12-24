#!/bin/bash
echo "=== Check activeVersionId ==="
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, name, active, \"activeVersionId\", \"versionId\" FROM workflow_entity;"
