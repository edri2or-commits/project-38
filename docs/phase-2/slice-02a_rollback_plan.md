# Slice 2A Rollback Plan — N8N Deployment

**Version:** 2.0 (Revised - N8N Only)  
**Date:** 2025-12-15  
**Environment:** DEV (project-38-ai)  
**Status:** 📋 PLANNING (Not yet needed)

---

## Purpose

This plan provides step-by-step instructions to safely rollback Slice 2A deployment if:
- Deployment fails mid-execution
- Services fail health checks
- Critical errors discovered post-deployment
- User requests rollback

**Goal:** Return VM to clean Slice 1 state (Docker installed, no containers running)

**Scope:** Slice 2A deploys N8N only (2 services: postgres, n8n). Kernel not included.

---

## Rollback Scenarios

### Scenario A: Deployment Failed Before Services Started
**Symptoms:**
- docker-compose.yml creation failed
- Secret fetcher script failed
- No containers running

**Action:** Cleanup files only (no containers to stop)

### Scenario B: Partial Deployment (Some Containers Running)
**Symptoms:**
- Some containers started
- Not all health checks passing
- Errors in logs

**Action:** Stop containers + cleanup files

### Scenario C: Full Deployment But Needs Rollback
**Symptoms:**
- All containers running
- Critical bug discovered
- User requests rollback

**Action:** Full cleanup (containers + volumes + files)

---

## Rollback Procedure

### Pre-Rollback Checklist

**Before executing rollback:**
- [ ] Document WHY rollback is needed
- [ ] Capture final state (logs, container status)
- [ ] Confirm with user (if not emergency)
- [ ] Take evidence snapshot

**Evidence to capture:**
```bash
# Container status
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker compose ps > /tmp/rollback-snapshot.txt 2>&1"

# Logs
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker logs p38-postgres --tail 50 > /tmp/postgres-rollback.log 2>&1"

gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker logs p38-n8n --tail 50 > /tmp/n8n-rollback.log 2>&1"
```

---

## Step-by-Step Rollback

### Step 1: Stop All Containers

**Objective:** Gracefully stop all running containers

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="cd /home/\$(whoami) && docker compose down"
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Container p38-n8n       Removed
 ✔ Container p38-postgres  Removed
 ✔ Network project38-network  Removed
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker ps -a"
```

**Success Criteria:**
- No containers running
- Network removed
- Exit code 0

**If Step 1 Fails:**
```bash
# Force stop all containers
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker stop \$(docker ps -aq) && docker rm \$(docker ps -aq)"
```

---

### Step 2: Remove Docker Volumes (OPTIONAL)

**Objective:** Delete persistent data (Postgres DB, N8N workflows)

⚠️ **WARNING:** This deletes ALL data. Only do this if:
- Fresh start required
- Data is corrupted
- User explicitly requests

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker volume rm postgres_data n8n_data"
```

**Expected Output:**
```
postgres_data
n8n_data
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker volume ls"
```

**Success Criteria:**
- No volumes named postgres_data or n8n_data
- Exit code 0

**If Step 2 Fails:**
```bash
# Force remove volumes
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker volume rm -f postgres_data n8n_data"
```

---

### Step 3: Remove Deployment Files

**Objective:** Clean up docker-compose.yml and scripts

**Command:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="rm -rf /home/\$(whoami)/docker-compose.yml /home/\$(whoami)/load-secrets.sh"
```

**Expected Output:**
```
(no output - success)
```

**Verification:**
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="ls -la /home/\$(whoami)/ | grep -E 'docker-compose|load-secrets'"
```

**Success Criteria:**
- No output (files removed)
- Exit code 1 (grep found nothing)

---

### Step 4: Verify Clean State

**Objective:** Confirm VM is back to Slice 1 baseline

#### 4.1: Check No Containers Running
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker ps -a"
```

**Expected:**
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```
(Empty list)

#### 4.2: Check Docker Service
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="sudo systemctl status docker | head -5"
```

**Expected:**
```
● docker.service - Docker Application Container Engine
   Loaded: loaded
   Active: active (running)
```

#### 4.3: Check Files Removed
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="ls -la /home/\$(whoami)/"
```

**Expected:**
- No docker-compose.yml
- No load-secrets.sh

**Success Criteria:**
- ✅ Docker running
- ✅ No containers
- ✅ No deployment files
- ✅ VM accessible
- ✅ Static IP unchanged (136.111.39.139)

---

### Step 5: Close SSH Port-Forward (if running)

**Objective:** Stop SSH tunnel

**Action:** In the terminal where port-forward is running, press `Ctrl+C`

**Verification:**
Try accessing http://localhost:5678/ in browser

**Expected:** Connection refused (tunnel closed)

---

## Post-Rollback Actions

### 1. Update Documentation

**Files to update:**

#### traceability_matrix.md
```markdown
| Slice 2A | N8N Deployment | ❌ ROLLED BACK | [date] | [reason] |
```

#### Create rollback log
**Path:** `C:\Users\edri2\project_38\docs\phase-2\slice-02a_rollback_log.md`

**Template:**
```markdown
# Slice 2A Rollback Log

**Date:** [YYYY-MM-DD]
**Time:** [HH:MM:SS UTC]
**Executed By:** [Claude/User]
**Reason:** [Brief explanation]

## Rollback Steps Executed
- [X] Step 1: Containers stopped
- [X] Step 2: Volumes removed (Y/N)
- [X] Step 3: Files removed
- [X] Step 4: Clean state verified
- [X] Step 5: Port-forward closed

## Evidence
[Paste relevant outputs]

## Root Cause
[Why rollback was needed]

## Lessons Learned
[What to do differently next time]

## Next Steps
[Plan for re-attempt or alternative approach]
```

### 2. Preserve Evidence

**Save rollback artifacts:**
```bash
# Copy logs from VM to local
gcloud compute scp p38-dev-vm-01:/tmp/rollback-snapshot.txt \
  C:\Users\edri2\project_38\docs\phase-2\rollback-evidence\ \
  --zone=us-central1-a \
  --project=project-38-ai

gcloud compute scp p38-dev-vm-01:/tmp/*-rollback.log \
  C:\Users\edri2\project_38\docs\phase-2\rollback-evidence\ \
  --zone=us-central1-a \
  --project=project-38-ai
```

### 3. Notify User

**Status message:**
```
Slice 2A rolled back successfully.
VM returned to Slice 1 baseline (Docker installed, no containers).
Reason: [brief explanation]
Evidence: docs/phase-2/slice-02a_rollback_log.md
Ready for: [next action - re-attempt Slice 2A, investigate blocker, etc.]
```

---

## Partial Rollback (Emergency)

**If full rollback not possible:**

### Nuclear Option: Container Force Removal
```bash
gcloud compute ssh p38-dev-vm-01 \
  --zone=us-central1-a \
  --project=project-38-ai \
  --command="docker kill \$(docker ps -q) && docker rm -f \$(docker ps -aq) && docker volume prune -f && docker network prune -f"
```

⚠️ **Only use if:**
- Standard rollback failed
- Containers won't stop gracefully
- Critical issue requires immediate cleanup

---

## Recovery After Rollback

### Option A: Re-Attempt Slice 2A
**When:**
- Issue identified and fixed
- User wants to retry deployment

**Action:**
1. Review rollback log
2. Address root cause
3. Update runbook/code if needed
4. Re-execute Slice 2A from Step 1

### Option B: Investigate Before Retry
**When:**
- Root cause unclear
- Need debugging

**Action:**
1. Review error logs
2. Test individual components
3. Verify prerequisites again
4. Document findings
5. Update runbook
6. Get user approval for retry

### Option C: Alternative Approach
**When:**
- Docker Compose approach has issues
- Need different architecture

**Action:**
1. Document why current approach failed
2. Propose alternative (e.g., separate VMs per service)
3. Get user approval
4. Create new Slice 2A' runbook

---

## Rollback Checklist (Quick Reference)

**Before rollback:**
- [ ] Capture evidence (logs, container status)
- [ ] Document reason
- [ ] Get user confirmation (if not emergency)

**Rollback steps:**
- [ ] Stop containers (docker compose down)
- [ ] Remove volumes (if needed)
- [ ] Remove files (docker-compose.yml, scripts)
- [ ] Verify clean state
- [ ] Close SSH port-forward

**After rollback:**
- [ ] Update traceability_matrix.md
- [ ] Create rollback log
- [ ] Preserve evidence
- [ ] Notify user
- [ ] Plan next steps

---

## Important Notes

### What Rollback DOES NOT Affect

**Unchanged after rollback:**
- ✅ VM (p38-dev-vm-01) - still running
- ✅ Static IP (136.111.39.139) - still assigned
- ✅ Firewall rules - still active
- ✅ Docker Engine - still installed
- ✅ Docker Compose - still installed
- ✅ Service Account (n8n-runtime) - still attached
- ✅ IAM permissions - unchanged
- ✅ Secrets in GCP Secret Manager - unchanged

**Only removes:**
- ❌ Running containers (2: postgres, n8n)
- ❌ Docker volumes (if Step 2 executed)
- ❌ Deployment files (docker-compose.yml, load-secrets.sh)

### Rollback Is SAFE

**No risk of:**
- VM deletion
- IP address loss
- Secret deletion
- IAM permission changes
- Infrastructure damage

**Rollback scope:** Application layer only (containers + files)

---

## Troubleshooting

### Problem: docker compose down fails

**Symptom:**
```
Error response from daemon: ...
```

**Solution:**
```bash
# Force stop
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker stop \$(docker ps -q); docker rm \$(docker ps -aq)"
```

### Problem: Volume removal fails (in use)

**Symptom:**
```
Error response from daemon: remove postgres_data: volume is in use
```

**Solution:**
```bash
# Ensure all containers stopped first
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker ps -aq | xargs docker rm -f"

# Then retry volume removal
gcloud compute ssh p38-dev-vm-01 --zone=us-central1-a --project=project-38-ai \
  --command="docker volume rm -f postgres_data n8n_data"
```

### Problem: SSH connection fails during rollback

**Symptom:**
```
ssh: connect to host ... port 22: Connection timed out
```

**Solution:**
```bash
# Use GCP Console Serial Console
# Navigate to: Compute Engine > VM Instances > p38-dev-vm-01 > Connect > Serial Console
# Execute commands directly
```

---

**End of Rollback Plan**

**Status:** Ready for use if Slice 2A execution encounters issues.

**Scope:** Slice 2A deploys N8N only (2 services). Kernel not included in this slice.
