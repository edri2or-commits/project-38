# Slice 1 Rollback Plan — VM Baseline (DEV)

**Phase:** Slice 1 (Infrastructure - VM Baseline)  
**Environment:** DEV (project-38-ai)  
**Status:** Rollback template (use only if execution fails)  
**Created:** 2024-12-15

---

## Purpose

Minimal cleanup plan to revert Slice 1 changes if execution fails or needs to be aborted.

**When to Use:**
- Execution encounters fatal error (see Stop Conditions in runbook)
- User requests rollback before completion
- Need to retry Slice 1 from clean state

**Rule:** Rollback in REVERSE order of creation (delete VM first, IP last)

---

## Rollback Order (LIFO - Last In, First Out)

1. Delete VM Instance
2. Delete Firewall Rules (3 rules)
3. Release Static IP

---

## Step 1: Delete VM Instance

**Purpose:** Remove the compute instance (will release IP automatically if in use)

### Command
```bash
gcloud compute instances delete project-38-dev-vm-01 \
  --zone=<ZONE> \
  --project=project-38-ai \
  --quiet
```

**Flags:**
- `--quiet`: Skip confirmation prompt (auto-confirm deletion)

**Verification:**
```bash
gcloud compute instances list \
  --filter="name=project-38-dev-vm-01" \
  --project=project-38-ai
```

**Expected Output:**
```
Listed 0 items.
```

**If Deletion Fails:**
- Check if VM is already deleted: `gcloud compute instances list --project=project-38-ai`
- If VM stuck in stopping state: wait 2-3 minutes, retry
- If VM deletion blocked: check for attached disks or labels preventing deletion

---

## Step 2: Delete Firewall Rules

**Purpose:** Remove the 3 ingress rules created for this VM

### Rule 1: Delete SSH Rule
```bash
gcloud compute firewall-rules delete project-38-dev-allow-ssh \
  --project=project-38-ai \
  --quiet
```

### Rule 2: Delete HTTP Rule
```bash
gcloud compute firewall-rules delete project-38-dev-allow-http \
  --project=project-38-ai \
  --quiet
```

### Rule 3: Delete HTTPS Rule
```bash
gcloud compute firewall-rules delete project-38-dev-allow-https \
  --project=project-38-ai \
  --quiet
```

**Verification:**
```bash
gcloud compute firewall-rules list \
  --filter="name~'project-38-dev-'" \
  --project=project-38-ai
```

**Expected Output:**
```
Listed 0 items.
```

**If Deletion Fails:**
- Rule not found: likely already deleted (check list)
- Permission error: verify account has compute.firewalls.delete permission
- Rule in use: should not happen if VM already deleted

---

## Step 3: Release Static IP

**Purpose:** Delete the reserved external IP address

### Command
```bash
gcloud compute addresses delete project-38-dev-vm-01-ip \
  --region=<REGION> \
  --project=project-38-ai \
  --quiet
```

**Verification:**
```bash
gcloud compute addresses list \
  --filter="name=project-38-dev-vm-01-ip" \
  --project=project-38-ai
```

**Expected Output:**
```
Listed 0 items.
```

**If Deletion Fails:**
- IP still in use: verify VM is fully deleted first (Step 1)
- IP not found: likely already released (check list)
- Wait 1-2 minutes after VM deletion, then retry

---

## Full Rollback Script (One-Shot)

**Use with caution — deletes all Slice 1 resources at once.**

```bash
#!/bin/bash

# Slice 1 Rollback Script
# Run from local machine with gcloud configured

set -e  # Exit on error

PROJECT="project-38-ai"
ZONE="<ZONE>"           # Replace with actual zone
REGION="<REGION>"       # Replace with actual region

echo "Starting Slice 1 rollback for project: $PROJECT"

# Step 1: Delete VM
echo "Deleting VM instance..."
gcloud compute instances delete project-38-dev-vm-01 \
  --zone=$ZONE \
  --project=$PROJECT \
  --quiet || echo "VM already deleted or not found"

# Wait for VM deletion to propagate
sleep 10

# Step 2: Delete Firewall Rules
echo "Deleting firewall rules..."
gcloud compute firewall-rules delete project-38-dev-allow-ssh \
  --project=$PROJECT \
  --quiet || echo "SSH rule already deleted"

gcloud compute firewall-rules delete project-38-dev-allow-http \
  --project=$PROJECT \
  --quiet || echo "HTTP rule already deleted"

gcloud compute firewall-rules delete project-38-dev-allow-https \
  --project=$PROJECT \
  --quiet || echo "HTTPS rule already deleted"

# Step 3: Release Static IP
echo "Releasing static IP..."
gcloud compute addresses delete project-38-dev-vm-01-ip \
  --region=$REGION \
  --project=$PROJECT \
  --quiet || echo "Static IP already released"

echo "Rollback complete. Verifying cleanup..."

# Verification
echo ""
echo "=== Verification ==="
echo "VMs remaining:"
gcloud compute instances list --project=$PROJECT

echo ""
echo "Firewall rules remaining (should not include project-38-dev-*):"
gcloud compute firewall-rules list --filter="name~'project-38-dev-'" --project=$PROJECT

echo ""
echo "Static IPs remaining (should not include project-38-dev-vm-01-ip):"
gcloud compute addresses list --project=$PROJECT

echo ""
echo "Rollback verification complete."
```

**Save as:** `rollback_slice_01.sh`

**Execute:**
```bash
chmod +x rollback_slice_01.sh
./rollback_slice_01.sh
```

---

## Partial Rollback Scenarios

### Scenario A: Only VM Created (IP + Firewall Rules Not Yet Created)
**Rollback:**
```bash
gcloud compute instances delete project-38-dev-vm-01 \
  --zone=<ZONE> \
  --project=project-38-ai \
  --quiet
```

### Scenario B: IP + Firewall Rules Created, VM Failed
**Rollback:**
```bash
# Delete firewall rules
gcloud compute firewall-rules delete project-38-dev-allow-ssh --project=project-38-ai --quiet
gcloud compute firewall-rules delete project-38-dev-allow-http --project=project-38-ai --quiet
gcloud compute firewall-rules delete project-38-dev-allow-https --project=project-38-ai --quiet

# Release IP
gcloud compute addresses delete project-38-dev-vm-01-ip --region=<REGION> --project=project-38-ai --quiet
```

### Scenario C: VM Running, But Docker Installation Failed
**Decision Point:** Keep or rollback?

**Option 1: Keep VM, retry Docker installation**
- SSH to VM: `gcloud compute ssh project-38-dev-vm-01 --zone=<ZONE> --project=project-38-ai`
- Re-run Docker installation steps from runbook

**Option 2: Full rollback and retry**
- Follow full rollback (Steps 1-3)
- Retry Slice 1 from beginning

### Scenario D: Secret Access Validation Failed
**Diagnosis:** IAM issue, not infrastructure issue

**Rollback Decision:** DO NOT rollback infrastructure
- VM and network are fine
- Fix IAM permissions (check `secret_sync_history.md` for correct bindings)
- Re-run secret validation step only

---

## Post-Rollback Actions

After successful rollback:

1. **Update traceability_matrix.md:**
   - Slice 1 status: ❌ FAILED (rollback completed)
   - Add failure reason + timestamp
   - Link to execution log (if one exists)

2. **Document Failure:**
   - Create `slice-01_failure_report.md` in `docs/phase-2/`
   - Include: failure reason, rollback timestamp, lessons learned
   - Attach any error messages or logs

3. **Wait Before Retry:**
   - Give GCP time to propagate deletions (2-5 minutes)
   - Verify all resources removed (see verification commands above)

4. **Fix Root Cause:**
   - If quota issue: request quota increase
   - If IAM issue: fix service account permissions
   - If region issue: choose different region/zone
   - If network issue: check VPC/firewall defaults

5. **Ready for Retry:**
   - Verify cleanup complete
   - Get user approval
   - Re-run Slice 1 from beginning

---

## Emergency Rollback (Manual via Console)

If gcloud CLI is unavailable or failing:

### Via Google Cloud Console:

1. **Delete VM:**
   - Go to: Compute Engine > VM Instances
   - Select `project-38-dev-vm-01`
   - Click "Delete" (top menu)
   - Confirm deletion

2. **Delete Firewall Rules:**
   - Go to: VPC Network > Firewall
   - Filter by: `project-38-dev-`
   - Select all 3 rules (ssh, http, https)
   - Click "Delete"
   - Confirm deletion

3. **Release Static IP:**
   - Go to: VPC Network > IP Addresses
   - Find: `project-38-dev-vm-01-ip`
   - Click "Release" (if status is RESERVED)
   - If status is IN_USE: delete VM first, then release

---

## Cost Implications of Rollback

- **VM Deletion:** No further charges after deletion (billed by minute)
- **Static IP Deletion:** Charges stop immediately
- **Firewall Rules:** No charges (free resource)
- **Boot Disk:** Deleted automatically with VM (no orphan disk)

**Expected Cost Recovery:** Full (no lingering charges after rollback)

---

## Rollback Verification Checklist

After rollback, verify:

- [ ] VM deleted: `gcloud compute instances list --project=project-38-ai` shows 0 items
- [ ] Firewall rules deleted: `gcloud compute firewall-rules list --filter="name~'project-38-dev-'" --project=project-38-ai` shows 0 items
- [ ] Static IP released: `gcloud compute addresses list --project=project-38-ai` does not show `project-38-dev-vm-01-ip`
- [ ] No orphan disks: `gcloud compute disks list --filter="name~'project-38-dev-'" --project=project-38-ai` shows 0 items
- [ ] Traceability matrix updated with rollback timestamp
- [ ] User notified of rollback completion

**If ALL checked:** Rollback is complete and verified ✅

---

## Notes

- **Rollback Duration:** 5-10 minutes (mostly waiting for deletions to propagate)
- **Idempotent:** Safe to run multiple times (ignores "not found" errors)
- **No Data Loss:** VM had no workloads deployed yet (Slice 1 is infrastructure only)
- **Retry Safe:** After successful rollback, can retry Slice 1 from clean slate

---

## DO NOT Rollback These (They Are NOT Part of Slice 1)

❌ Do NOT delete service accounts (they were created in PRE-BUILD, not Slice 1)  
❌ Do NOT delete secrets (they were created in PRE-BUILD, not Slice 1)  
❌ Do NOT modify IAM bindings (not part of Slice 1)  
❌ Do NOT delete default VPC (we are using it, not creating it)

**Slice 1 Only Creates:**
1. Static IP
2. 3 Firewall rules
3. VM instance

**Only these 3 resource types should be rolled back.**
