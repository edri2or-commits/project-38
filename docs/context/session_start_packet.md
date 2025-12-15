# Session Start Packet — Project 38 V2

**Last Updated:** 2025-12-15  
**Purpose:** Minimal paste to start any new Claude session with correct context

---

## How to Use This

**At the start of EVERY new session:**
1. Paste the "Copy-Paste Template" below to Claude
2. Claude reads core files from repo
3. Claude prints 5-8 line snapshot
4. Claude awaits explicit instruction

**No Drive docs required.** Repo is SSOT.

---

## Copy-Paste Template (Use This Every Session)

```
Project 38 V2 Session Start
Repo: https://github.com/edri2or-commits/project-38
Workdir: C:\Users\edri2\project_38
DEV: project-38-ai
PROD: project-38-ai-prod

READ THESE FIRST (in order):
1. docs/context/operating_rules.md
2. docs/context/project_facts.md
3. docs/traceability_matrix.md

VERIFY KEY HASHES:
- slice-02a_runbook.md: 3C26E6A0BE30D7A8E43B97087896A50EDB07F41BBFB43B5837347B084676931E
- slice-02a_evidence_pack.md: 7211B93373C3085096AFCE3183FD4AEAD55832E3CD00E061E75DD9670B7A7170
- slice-02a_rollback_plan.md: 71F5146C7A0921F91F4DCE020BC4D35B746BA1F7C775367C554C71C18ADA06E0

PRINT SNAPSHOT (5-8 lines):
✅ DONE: [completed items]
📋 NEXT: [immediate next step]
⏸️ DEFERRED: [postponed items]
🎯 Ready to: [action based on user request]

STOP LINE: No cloud actions (gcloud/VM/Docker/deploy) unless user says:
- "Execute Slice 2A" (for N8N deployment)
- "Execute Slice 2B" (for Kernel deployment)
- Other explicit approval text

READY.
```

---

## What Claude Does After Receiving This

### Step 1: Read Core Files
Claude reads these 3 files in order:
1. `docs/context/operating_rules.md` — Operating protocols
2. `docs/context/project_facts.md` — Immutable facts
3. `docs/traceability_matrix.md` — Current status + evidence

### Step 2: Verify Hashes (Optional)
If critical files have hash mismatches, Claude flags it:
- **Expected hash:** From session start packet
- **Actual hash:** From file content
- **If mismatch:** Warn user, don't proceed

### Step 3: Print Snapshot
Claude prints a 5-8 line status snapshot:
```
📸 Snapshot:
✅ DONE: Slice 1 (VM baseline + Docker + IAM verified), Slice 2 split (2A=N8N+Postgres planned, 2B/3=Kernel deferred)
📋 NEXT: Establish SSOT-in-repo + Evidence store (no Drive), then Slice 2A execution only with explicit "Execute Slice 2A"
⏸️ DEFERRED: Slice 2B/3 Kernel (separate VM recommended), Slice 3/4
🎯 Ready to: [respond to user request]
```

### Step 4: Await Instruction
Claude does NOT execute any action until user provides explicit instruction:
- ✅ **Approved:** "Execute Slice 2A", "Run Slice 2B", "Deploy to PROD"
- ❌ **Not approved:** "What's the status?", "Can you help with X?", "Show me Y"

---

## Snapshot Format Template

Use this format for consistency:

```
📸 Snapshot:
✅ DONE: [Phase X completed items] + [Slice Y status]
📋 NEXT: [Immediate next step or blocker]
⏸️ DEFERRED: [Postponed items]
🎯 Ready to: [action based on user request or "awaiting instruction"]
```

### Examples

**Example 1: After Slice 1 Complete**
```
📸 Snapshot:
✅ DONE: Slice 1 (VM + Docker + IAM + 7 secrets verified in DEV)
📋 NEXT: Slice 2A (N8N+Postgres deployment) - runbook ready, awaiting "Execute Slice 2A"
⏸️ DEFERRED: Slice 2B/3 (Kernel - SA architecture TBD)
🎯 Ready to: [user request]
```

**Example 2: After Slice 2A Complete**
```
📸 Snapshot:
✅ DONE: Slice 1 (infra), Slice 2A (N8N+Postgres deployed, validated)
📋 NEXT: Slice 2B/3 (Kernel deployment) - pending SA architecture decision
⏸️ DEFERRED: Slice 3 (testing), Slice 4 (PROD mirror)
🎯 Ready to: [user request]
```

**Example 3: Blocked State**
```
📸 Snapshot:
✅ DONE: Slice 1 (infra), Slice 2A (N8N+Postgres)
📋 NEXT: BLOCKED - Kernel SA architecture decision required (Option A: separate VM, Option B: multi-SA same VM)
⏸️ DEFERRED: Slice 3/4
🎯 Ready to: Discuss SA options or await decision
```

---

## File Hashes (Update After Changes)

**Current verified hashes (2025-12-15):**

| File | SHA256 (first 64 chars) | Size | Purpose |
|------|-------------------------|------|---------|
| slice-02a_runbook.md | 3C26E6A0BE30D7A8E43B97087896A50EDB07F41BBFB43B5837347B084676931E | 20,664 bytes | N8N deployment steps |
| slice-02a_evidence_pack.md | 7211B93373C3085096AFCE3183FD4AEAD55832E3CD00E061E75DD9670B7A7170 | 9,180 bytes | Evidence template |
| slice-02a_rollback_plan.md | 71F5146C7A0921F91F4DCE020BC4D35B746BA1F7C775367C554C71C18ADA06E0 | 11,300 bytes | Rollback procedures |

**How to verify:**
```bash
# Windows (PowerShell)
Get-FileHash -Path "C:\Users\edri2\project_38\docs\phase-2\slice-02a_runbook.md" -Algorithm SHA256

# Linux/Mac
sha256sum C:\Users\edri2\project_38\docs\phase-2\slice-02a_runbook.md
```

**When to update hashes:**
- After editing any critical file
- After completing a slice (execution log changes)
- After major refactoring

---

## Required Files (Must Exist in Repo)

Claude needs these files to operate correctly:

### Core Context Files (docs/context/)
- ✅ `operating_rules.md` — Anti-chaos protocols
- ✅ `project_facts.md` — Immutable facts (projects, repos, paths)
- ✅ `gcp_state_snapshot.md` — Current GCP resource state
- ✅ `phase_status.md` — Current phase/slice progress
- ✅ `ssot_and_evidence_protocol.md` — This system's documentation
- ✅ `session_start_packet.md` — This file

### Traceability (docs/)
- ✅ `traceability_matrix.md` — Component status + evidence links

### Phase 2 Artifacts (docs/phase-2/)
- ✅ `slice-01_runbook.md` — Slice 1 execution plan
- ✅ `slice-01_execution_log.md` — Slice 1 evidence
- ✅ `slice-01_evidence_pack.md` — Slice 1 evidence template
- ✅ `slice-01_rollback_plan.md` — Slice 1 rollback
- ✅ `slice-02a_runbook.md` — Slice 2A execution plan
- ✅ `slice-02a_evidence_pack.md` — Slice 2A evidence template
- ✅ `slice-02a_rollback_plan.md` — Slice 2A rollback

### Evidence Manifest (docs/evidence/)
- ✅ `manifest.md` — Evidence artifact registry

---

## Stop Conditions (CRITICAL)

**Claude MUST NOT execute these actions without explicit approval:**

### ❌ Forbidden Without Approval
- Run gcloud commands (except metadata reads)
- SSH into VM
- Execute Docker/Compose commands
- Create/modify GCP resources
- Deploy workloads
- Modify IAM policies
- Access secret values
- Push to PROD

### ✅ Always Allowed
- Read repo files
- Print snapshots
- Answer questions
- Explain concepts
- Generate documentation
- Calculate hashes
- Verify evidence integrity

### 🟡 Requires Explicit Approval
**User must say one of these phrases:**
- "Execute Slice 2A" → Deploy N8N + Postgres
- "Execute Slice 2B" → Deploy Kernel
- "Run Slice 3" → Testing & validation
- "Deploy to PROD" → PROD mirror
- "LEGACY_WRITE_OK" → Write to legacy workspace

**If user does NOT use approval phrase:**
- Assume DOCS ONLY mode
- No cloud actions
- Provide documentation, guidance, planning only

---

## Troubleshooting

### Issue: Hash mismatch
**Symptom:** SHA256 doesn't match session start packet  
**Fix:** 
1. Check if file was edited since packet created
2. Recalculate hash: `Get-FileHash -Path "..." -Algorithm SHA256`
3. Update session start packet with new hash
4. Commit to repo

### Issue: File not found
**Symptom:** Claude can't read a required file  
**Fix:**
1. Verify file exists in workdir: `C:\Users\edri2\project_38\docs\...`
2. Check file permissions (read access required)
3. Ensure repo is up-to-date: `git pull origin main`

### Issue: Outdated snapshot
**Symptom:** Snapshot doesn't match current state  
**Fix:**
1. Read `docs/context/phase_status.md` for current state
2. Read `docs/traceability_matrix.md` for latest status
3. Print updated snapshot with correct status

### Issue: Claude tries to execute without approval
**Symptom:** Claude runs gcloud/Docker commands without user saying "Execute Slice X"  
**Fix:**
1. User: Say "STOP — no execution without my approval"
2. Claude: Acknowledge, switch to DOCS ONLY mode
3. User: Provide explicit approval when ready

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-15 | 1.0 | Initial creation (Drive deprecation) |

---

## Next Updates Required

Update this file when:
- New slice completed (add new hash to verification section)
- Phase progression (update snapshot examples)
- New critical files added (add to required files list)
- Stop conditions change (update forbidden/allowed actions)

**Keep this file under 500 lines** — move detailed docs to other files if needed.
