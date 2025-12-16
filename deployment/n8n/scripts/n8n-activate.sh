#!/bin/bash
# n8n-activate.sh — Headless workflow activation with guardrails
# Project 38 — DO NOT USE IN PRODUCTION WITHOUT REVIEW
#
# Usage: ./n8n-activate.sh <workflow_json_path> [--dry-run]
#
# This script works around n8n CLI limitations by:
# 1. Importing workflow via CLI
# 2. Creating workflow_history record (required for activation)
# 3. Setting active=true + activeVersionId
# 4. Restarting n8n container

set -euo pipefail

# --- Configuration ---
N8N_CONTAINER="p38-n8n"
PG_CONTAINER="p38-postgres"
PG_USER="n8n"
PG_DB="n8n"
RESTART_WAIT=20

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Functions ---
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

psql_exec() {
    docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -t -c "$1" 2>/dev/null | tr -d ' '
}

psql_exec_verbose() {
    docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c "$1"
}

# --- Argument Parsing ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <workflow_json_path> [--dry-run]"
    exit 1
fi

WORKFLOW_JSON="$1"
DRY_RUN=false
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=true

if [[ ! -f "$WORKFLOW_JSON" ]]; then
    log_error "File not found: $WORKFLOW_JSON"
    exit 1
fi

# --- Extract workflow name from JSON ---
WF_NAME=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$WORKFLOW_JSON" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/')
if [[ -z "$WF_NAME" ]]; then
    log_error "Could not extract workflow name from JSON"
    exit 1
fi

log_info "Workflow: $WF_NAME"
log_info "Dry run: $DRY_RUN"

# --- Pre-flight checks ---
log_info "Checking containers..."
if ! docker ps --format '{{.Names}}' | grep -q "^${N8N_CONTAINER}$"; then
    log_error "Container $N8N_CONTAINER not running"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q "^${PG_CONTAINER}$"; then
    log_error "Container $PG_CONTAINER not running"
    exit 1
fi
log_info "Containers OK"

# --- Check if workflow already exists ---
EXISTING_ID=$(psql_exec "SELECT id FROM workflow_entity WHERE name='$WF_NAME' LIMIT 1;")
if [[ -n "$EXISTING_ID" ]]; then
    log_warn "Workflow '$WF_NAME' already exists (ID: $EXISTING_ID)"
    read -p "Delete and reimport? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            psql_exec "DELETE FROM workflow_history WHERE \"workflowId\"='$EXISTING_ID';"
            psql_exec "DELETE FROM workflow_entity WHERE id='$EXISTING_ID';"
            log_info "Deleted existing workflow"
        else
            log_info "[DRY-RUN] Would delete workflow $EXISTING_ID"
        fi
    else
        log_error "Aborted"
        exit 1
    fi
fi

# --- Step 1: Import workflow ---
log_info "Step 1/5: Importing workflow..."
if [[ "$DRY_RUN" == "false" ]]; then
    docker cp "$WORKFLOW_JSON" "$N8N_CONTAINER:/tmp/workflow_import.json"
    docker exec "$N8N_CONTAINER" n8n import:workflow --input=/tmp/workflow_import.json 2>&1 || {
        log_error "Import failed"
        exit 1
    }
else
    log_info "[DRY-RUN] Would import $WORKFLOW_JSON"
fi

# --- Step 2: Get workflow ID ---
log_info "Step 2/5: Getting workflow ID..."
sleep 2
WF_ID=$(psql_exec "SELECT id FROM workflow_entity WHERE name='$WF_NAME' LIMIT 1;")
if [[ -z "$WF_ID" ]]; then
    log_error "Could not find imported workflow in DB"
    exit 1
fi
log_info "Workflow ID: $WF_ID"

# --- Step 3: Get versionId ---
VERSION_ID=$(psql_exec "SELECT \"versionId\" FROM workflow_entity WHERE id='$WF_ID';")
if [[ -z "$VERSION_ID" ]]; then
    log_error "Workflow has no versionId"
    exit 1
fi
# Trim whitespace
VERSION_ID=$(echo "$VERSION_ID" | xargs)
log_info "Version ID: $VERSION_ID"

# --- Step 4: Create history record (in transaction) ---
log_info "Step 3/5: Creating history record..."
HISTORY_EXISTS=$(psql_exec "SELECT COUNT(*) FROM workflow_history WHERE \"workflowId\"='$WF_ID' AND \"versionId\"='$VERSION_ID';")
if [[ "$HISTORY_EXISTS" -gt 0 ]]; then
    log_warn "History record already exists, skipping"
else
    if [[ "$DRY_RUN" == "false" ]]; then
        psql_exec_verbose "
        BEGIN;
        INSERT INTO workflow_history 
            (\"versionId\", \"workflowId\", authors, \"createdAt\", \"updatedAt\", nodes, connections, name, autosaved)
        SELECT 
            '$VERSION_ID', id, '[]', NOW(), NOW(), nodes, connections, name, false 
        FROM workflow_entity 
        WHERE id='$WF_ID';
        COMMIT;
        " || {
            log_error "Failed to create history record"
            exit 1
        }
    else
        log_info "[DRY-RUN] Would insert history record"
    fi
fi

# --- Step 5: Activate workflow ---
log_info "Step 4/5: Activating workflow..."
if [[ "$DRY_RUN" == "false" ]]; then
    psql_exec_verbose "
    BEGIN;
    UPDATE workflow_entity 
    SET active=true, \"activeVersionId\"='$VERSION_ID' 
    WHERE id='$WF_ID';
    COMMIT;
    " || {
        log_error "Failed to activate workflow"
        exit 1
    }
else
    log_info "[DRY-RUN] Would set active=true, activeVersionId=$VERSION_ID"
fi

# --- Step 6: Restart n8n ---
log_info "Step 5/5: Restarting n8n..."
if [[ "$DRY_RUN" == "false" ]]; then
    docker restart "$N8N_CONTAINER"
    log_info "Waiting ${RESTART_WAIT}s for n8n to start..."
    sleep "$RESTART_WAIT"
else
    log_info "[DRY-RUN] Would restart $N8N_CONTAINER"
fi

# --- Verification ---
log_info "Verifying activation..."
if [[ "$DRY_RUN" == "false" ]]; then
    ACTIVE_CHECK=$(psql_exec "SELECT active FROM workflow_entity WHERE id='$WF_ID';")
    ACTIVE_VERSION=$(psql_exec "SELECT \"activeVersionId\" FROM workflow_entity WHERE id='$WF_ID';")
    
    if [[ "$ACTIVE_CHECK" == "t" ]] && [[ -n "$ACTIVE_VERSION" ]]; then
        log_info "✅ Workflow activated successfully"
        log_info "   ID: $WF_ID"
        log_info "   Active: true"
        log_info "   ActiveVersionId: $ACTIVE_VERSION"
        
        # Check n8n logs for activation
        ACTIVATED=$(docker logs "$N8N_CONTAINER" 2>&1 | tail -20 | grep -c "Activated workflow.*$WF_ID" || true)
        if [[ "$ACTIVATED" -gt 0 ]]; then
            log_info "✅ Confirmed in n8n logs"
        else
            log_warn "Not found in recent logs (may need more time)"
        fi
    else
        log_error "Activation verification failed"
        exit 1
    fi
else
    log_info "[DRY-RUN] Would verify activation"
fi

log_info "Done!"
