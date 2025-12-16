# POC-01: Headless Webhook Activation + Security Hardening

**Status:** ✅ PASS  
**Date:** 2025-12-16  
**Environment:** p38-dev-vm-01 (136.111.39.139)  
**n8n Version:** 2.0.2

---

## Objective

Verify that n8n workflows can be:
1. Imported and activated **headless** (CLI only, no UI)
2. Respond to webhook calls with HTTP 200
3. Run with security hardening enabled

---

## Root Cause Discovery

### The Bug: `active=true` Is Not Enough

n8n v2.x introduced **workflow versioning**. Setting `active=true` in DB is insufficient.

**Required fields for activation:**
| Field | Purpose |
|-------|---------|
| `active` | Boolean flag |
| `activeVersionId` | Must point to valid `workflow_history.versionId` |
| `workflow_history` record | Must exist with matching `versionId` |

**Without `activeVersionId`:** Workflow appears active in DB but n8n ignores it on startup.

### CLI Bug

`n8n publish:workflow` and `n8n update:workflow --active=true` fail with:
```
Version "v1-xxx" not found for workflow "ID"
```

**Cause:** CLI doesn't create `workflow_history` record on import.  
**Issue:** Not found in official GitHub issues as of 2025-12-16. May be intended behavior (versioning = Enterprise feature).

---

## Canonical Activation Sequence

```bash
# 1. IMPORT workflow JSON
docker cp workflow.json p38-n8n:/tmp/workflow.json
docker exec p38-n8n n8n import:workflow --input=/tmp/workflow.json

# 2. GET workflow ID
WF_ID=$(docker exec p38-n8n n8n list:workflow | grep "WorkflowName" | cut -d'|' -f1)

# 3. CREATE history record (workaround)
docker exec p38-postgres psql -U n8n -d n8n -c "
  INSERT INTO workflow_history 
    (\"versionId\", \"workflowId\", authors, \"createdAt\", \"updatedAt\", nodes, connections, name, autosaved)
  SELECT 
    \"versionId\", id, '[]', NOW(), NOW(), nodes, connections, name, false 
  FROM workflow_entity 
  WHERE id='${WF_ID}';"

# 4. SET active + activeVersionId
docker exec p38-postgres psql -U n8n -d n8n -c "
  UPDATE workflow_entity 
  SET active=true, \"activeVersionId\"=\"versionId\" 
  WHERE id='${WF_ID}';"

# 5. RESTART n8n (required for webhook registration)
docker restart p38-n8n
sleep 20

# 6. VERIFY
curl -s http://localhost:5678/webhook/<path>
# Expected: HTTP 200
```

---

## Security Hardening (Verified Active)

**docker-compose.yml environment:**
```yaml
N8N_BLOCK_ENV_ACCESS_IN_NODE: 'true'    # Blocks {{ $env.SECRET }}
NODES_EXCLUDE: 'n8n-nodes-base.executeCommand,n8n-nodes-base.readWriteFile'
N8N_SECURE_COOKIE: 'true'
```

**Effect:** Workflows cannot:
- Access environment variables via expressions
- Execute shell commands
- Read/write arbitrary files

---

## Rollback Procedure

If activation breaks something:

```bash
# 1. Deactivate workflow
docker exec p38-postgres psql -U n8n -d n8n -c "
  UPDATE workflow_entity 
  SET active=false, \"activeVersionId\"=NULL 
  WHERE id='<WORKFLOW_ID>';"

# 2. Optionally delete history
docker exec p38-postgres psql -U n8n -d n8n -c "
  DELETE FROM workflow_history 
  WHERE \"workflowId\"='<WORKFLOW_ID>';"

# 3. Restart
docker restart p38-n8n
```

**Safe because:** Each workflow isolated. FK constraints prevent orphan records.

---

## Warnings & Constraints

| ⚠️ Warning | Mitigation |
|------------|------------|
| Direct DB manipulation | Use provided script with transactions |
| `versionId` must be unique per workflow | Script auto-generates from workflow's own versionId |
| Restart required after activation | Built into canonical sequence |
| History FK constraint | Always insert history BEFORE setting activeVersionId |

---

## Test Evidence

See: `docs/evidence/poc-01/` for:
- `before_activation.txt` — DB state before
- `after_activation.txt` — DB state after
- `curl_output.txt` — HTTP 200 proof
- `commands_executed.txt` — Full command log

---

## Conclusion

**Headless activation works** with DB workaround. Production deployment should use `n8n-activate.sh` script (see `deployment/n8n/scripts/`).
