#!/bin/bash
docker exec p38-postgres psql -U n8n -d n8n -c "SELECT id, name, active FROM workflow_entity"
