# Operating Rules — Project 38 (V2)

**Last Updated:** 2025-12-15  
**Scope:** Anti-chaos rules for Project 38 operations

---

## Core Rule: Controlled Deployment Progression

**Current Status:**
- ✅ **Slice 1 DONE:** Infrastructure baseline (VM + Docker + IAM verified)
- 📋 **Slice 2A PLANNED:** N8N deployment (runbook ready, not yet executed)
- ⏸️ **Slice 2B/3 DEFERRED:** Kernel deployment (pending SA architecture decision)

**Operating Principle:** NO NEW BUILD/DEPLOY without explicit user instruction.

⚠️ **Each Slice requires explicit approval before execution.**

---

## Session Start Hook (MANDATORY)

**Apply at the start of EVERY conversation/session:**

### Required Actions (Before Any Work)
1. **Read Session Start Packet:**
   - `docs/context/session_start_packet.md` (copy-paste template provided there)

2. **Read these 3 core files:**
   - `docs/context/project_facts.md`
   - `docs/context/operating_rules.md` (this file)
   - `docs/traceability_matrix.md`

3. **Print Snapshot (5-8 lines):**
   ```
   📸 Snapshot:
   ✅ DONE: [list key completed items]
   📋 NEXT: [immediate next step]
   ⏸️ DEFERRED: [postponed items]
   🎯 Ready to: [what you're about to do based on user request]
   ```

4. **Do NOT execute any action before printing the Snapshot.**

### Why This Matters
- Ensures context continuity across sessions
- Prevents repeating DONE work (secrets, IAM)
- Reminds of phase (PRE-BUILD / Slice 1 / etc.)
- Aligns on NEXT steps before execution

### Example Snapshot
```
📸 Snapshot:
✅ DONE: Secrets (7×2), IAM (3 SA per project), Slice 1 (VM baseline)
📋 NEXT: Slice 2A (N8N deployment) - documentation ready, awaiting execution approval
⏸️ DEFERRED: Slice 2B/3 (Kernel), Cloud SQL/NAT/VPC (optional, Phase 2B/3)
🎯 Ready to: [analyze user request and determine action]
```

**Rule:** No action without Snapshot first.

---

## Rule 1: GCP Project Discipline (HARD LOCK)

### Mandatory --project Flag

**Every gcloud command MUST include:**
```bash
--project project-38-ai        # For DEV operations
--project project-38-ai-prod   # For PROD operations
```

### Forbidden Actions
❌ Never create resources in any other GCP project  
❌ Never assume default project  
❌ Never use project IDs like "edri2or-mcp" or any other non-project-38 ID

### Examples

**✅ CORRECT:**
```bash
gcloud secrets list --project=project-38-ai
gcloud compute instances list --project=project-38-ai-prod
```

**❌ WRONG:**
```bash
gcloud secrets list                    # Missing --project flag
gcloud secrets list --project=my-proj  # Wrong project ID
```

---

## Rule 2: Secret Discipline (ZERO TOLERANCE)

### Secrets Are DONE — Do NOT Recreate

**Status:** SYNC_OK / FINAL_OK / IAM_OK  
**Evidence:** 7 secrets × 2 projects, each with 2 ENABLED versions

### Forbidden Actions
❌ Do NOT create new secrets (they already exist)  
❌ Do NOT delete or disable existing secrets  
❌ Do NOT modify IAM bindings without documentation  
❌ Do NOT paste secret values in chat, files, Git, or logs  
❌ Do NOT access secret values without explicit instruction

### Allowed Actions (Metadata Only)
✅ List secret names: `gcloud secrets list --project=...`  
✅ Check IAM policy: `gcloud secrets get-iam-policy ... --project=...`  
✅ List versions: `gcloud secrets versions list ... --project=...`

### Verification During Deployment
When Slice 1 (Infrastructure) begins, secret access validation is allowed:
```bash
# Test secret access via service account impersonation
gcloud secrets versions access latest \
  --secret=openai-api-key \
  --project=project-38-ai \
  --impersonate-service-account=kernel-runtime@project-38-ai.iam.gserviceaccount.com
```

**Only perform this test when explicitly instructed for deployment validation.**

---

## Rule 3: IAM Discipline (Least Privilege)

### IAM Is DONE — Do NOT Recreate

**Status:** IAM_OK  
**Evidence:** 3 service accounts per project with documented least-privilege access

### Forbidden Actions
❌ Do NOT create new service accounts (they already exist)  
❌ Do NOT delete existing service accounts  
❌ Do NOT grant additional permissions without justification  
❌ Do NOT use wildcard permissions (e.g., `roles/*`)

### Service Account Summary (Read-Only Reference)
- **github-actions-deployer:** All 7 secrets (CI/CD needs)
- **n8n-runtime:** 3 secrets (workflow engine needs)
- **kernel-runtime:** 4 secrets + 2 project roles (agent needs)

See `secret_sync_history.md` for full access matrix.

---

## Rule 4: Legacy Workspace Quarantine

### Default: READ-ONLY

**Legacy Path:** `C:\Users\edri2\Desktop\AI\ai-os`

### Forbidden Actions (Unless LEGACY_WRITE_OK)
❌ Do NOT write files to legacy workspace  
❌ Do NOT modify legacy files  
❌ Do NOT execute build commands in legacy path  
❌ Do NOT commit changes to legacy repo (ai-os)

### Allowed Actions
✅ Read legacy files for reference  
✅ Inspect legacy configs for migration decisions  
✅ Compare legacy vs new implementations

### Override Keyword
User must explicitly provide: **LEGACY_WRITE_OK**

Only then are write operations allowed in legacy workspace.

---

## Rule 5: Repository Discipline

### Active Repository (Write-Enabled)
**URL:** https://github.com/edri2or-commits/project-38

✅ All commits go here  
✅ All PRs target this repo  
✅ CI/CD pipelines connected

### Legacy Repository (Read-Only)
**URL:** https://github.com/edri2or-commits/ai-os

❌ No commits unless user says **LEGACY_WRITE_OK**  
✅ Reference-only access

---

## Rule 6: Documentation Before Action

### Context Header (Every Response)
Always start responses with:
```
Working on: DEV/PROD projectId = ___, Workdir = ___, Repo = ___
```

### Evidence Before Claims
Never assume or guess. Use "Facts Block" as source of truth.

**If uncertain:**
1. Check `docs/context/` files first
2. Ask user for clarification
3. Do NOT proceed without facts

### Change Documentation
Before making infrastructure changes:
1. Document the change in `docs/context/`
2. Get user approval
3. Execute the change
4. Update traceability matrix

---

## Rule 7: SSOT Protocol (Repo-Based)

### Repo = Single Source of Truth

**SSOT Location:** This repository (`https://github.com/edri2or-commits/project-38`)

**Core SSOT Files:**
- `docs/context/project_facts.md` — Immutable facts
- `docs/context/operating_rules.md` — This file
- `docs/context/gcp_state_snapshot.md` — Current GCP state
- `docs/context/phase_status.md` — Phase/slice progress
- `docs/context/ssot_and_evidence_protocol.md` — SSOT system documentation
- `docs/context/session_start_packet.md` — Session initialization template
- `docs/traceability_matrix.md` — Component status + evidence links

### Evidence Store (External)
**Location:** `C:\Users\edri2\project_38__evidence_store\`

**Evidence Manifest:** `docs/evidence/manifest.md` (committed to repo)

**Evidence Files:** External storage, NOT committed to repo

**Verification:** SHA256 hashes in manifest ensure integrity

### Drive Status: DEPRECATED
**Drive is NO LONGER operational SSOT.**

**If user references Drive docs:**
1. Acknowledge politely
2. Redirect to repo-based SSOT
3. Use `docs/context/` files as truth
4. If conflict: repo takes precedence

**No Drive update requests needed** — all updates happen in repo via Git commits.

---

## Rule 8: DEV-First Approach

### Build Order
1. **DEV only** (project-38-ai)
2. Validate and test in DEV
3. Get user approval
4. **Then PROD** (project-38-ai-prod)

### Forbidden Actions
❌ Never deploy to PROD before DEV validation  
❌ Never mirror PROD → DEV (wrong direction)  
❌ Never make changes in both environments simultaneously

### Slice Progression
- ✅ Slice 1: DEV infrastructure baseline (DONE - VM + Docker + IAM verified)
- 📋 Slice 2A: DEV N8N deployment (PLANNED - awaiting execution approval)
- ⏸️ Slice 2B/3: DEV Kernel deployment (DEFERRED - SA architecture TBD)
- 📋 Slice 3: DEV testing & validation (pending Slice 2 completion)
- ⏸️ Slice 4: PROD mirror (pending DEV validation + approval)

---

## Rule 9: Anti-Chaos Checklist (Before Any Action)

### Ask Yourself:
1. ✅ Do I have the current status? (Slice 1 DONE, Slice 2A PLANNED, etc.)
2. ✅ Do I have explicit user instruction for this action?
3. ✅ Am I using the correct GCP project ID?
4. ✅ Am I writing to the NEW workspace (not legacy)?
5. ✅ Am I avoiding secret value exposure?
6. ✅ Am I not recreating existing resources?
7. ✅ Have I documented the context header?

**If any answer is NO → STOP and ask user for clarification.**

---

## Rule 10: Response Discipline

### Language
- **Default:** Hebrew (עברית)
- **Style:** Short, direct, structured
- **Format:** Copy-paste blocks for commands/templates

### Content Rules
❌ Never include secret values  
❌ Never assume facts not in documentation  
❌ Never skip context header  
✅ Always provide evidence for claims  
✅ Always structure outputs clearly (bullets, tables, code blocks)

### Example Response Structure:
```
Working on: [context header]

[Brief status/action summary]

[Detailed output/steps with code blocks or bullets]

[Next steps or questions]
```

---

## Rule 11: Evidence Pack Standard (For Execution Phases)

**Applies when executing deployment Slices (Slice 1 ✅ DONE, Slice 2+ pending approval)**

### Execution Log Location
Every Slice generates an execution log:
- **Location:** `docs/phase-2/slice-N_execution_log.md`
- **Format:** Markdown with clear sections

### Evidence Store Integration
- **Large artifacts:** Saved to `C:\Users\edri2\project_38__evidence_store\phase-2\slice-N\`
- **Manifest entry:** Added to `docs/evidence/manifest.md` with SHA256 hash
- **Repo summary:** Execution log includes excerpts + links to evidence store

### Required Contents (Evidence Pack)

#### 1. Timestamps
- Start time (ISO 8601 format)
- End time
- Duration
- Timestamp for each major step

#### 2. Exact Commands
- Full gcloud/docker/bash commands (copy-paste ready)
- Include ALL flags (especially `--project`)
- No abbreviations or summaries

#### 3. RAW Outputs
- Complete command outputs (stdout + stderr)
- **Redaction:** Replace actual secret values with `[REDACTED]`
- Keep structure/format intact for debugging
- **Full outputs:** Saved to evidence store
- **Excerpts:** Included in execution log (<10KB)
- Example:
  ```
  secret_value: [REDACTED]
  secret_name: openai-api-key
  secret_version: 2
  ```

#### 4. Verify Results
- Verification commands (e.g., `gcloud compute instances list`)
- Expected vs actual results
- Success/failure indicators

#### 5. Stop Condition Check
- What was the exit criteria for this Slice?
- Did we meet it? (Yes/No + evidence)
- If No: what's blocking + mitigation plan

#### 6. Artifacts Created
- List of resources created (VMs, IPs, firewall rules, etc.)
- Resource IDs and names
- Links to GCP Console (if applicable)

### Template Structure
```markdown
# Slice N Execution Log

**Date:** YYYY-MM-DD
**Start:** HH:MM:SS UTC
**End:** HH:MM:SS UTC
**Duration:** X minutes
**Executor:** Claude / User
**Status:** ✅ SUCCESS / ❌ FAILED / 🔄 PARTIAL

---

## Step 1: [Step Name]
**Timestamp:** HH:MM:SS UTC

### Command
\`\`\`bash
[exact command]
\`\`\`

### Output (Excerpt)
\`\`\`
[key output lines with redactions]
\`\`\`

**Full output:** See `phase-2/slice-N/step1_output.txt` (SHA256: abc123...)

### Verification
\`\`\`bash
[verification command]
\`\`\`

### Result
✅ SUCCESS / ❌ FAILED
[explanation]

---

[Repeat for each step]

---

## Stop Condition Check
**Exit Criteria:** [what we aimed to achieve]
**Met:** ✅ Yes / ❌ No
**Evidence:** [specific proof + evidence store references]

---

## Artifacts Created
- VM: `project-38-dev-vm-1` (ID: 123456789)
- Static IP: `34.56.78.90`
- Firewall rules: `allow-ssh`, `allow-http`, `allow-https`

---

## Next Steps
[What comes after this Slice]
```

### No "Done" Without Evidence
**Rule:** A Slice is NOT complete until:
1. Execution log exists (with excerpts)
2. Evidence artifacts saved to evidence store
3. Manifest updated with SHA256 hashes
4. All sections filled (timestamps, commands, outputs, verification)
5. Stop condition check passed
6. Traceability matrix updated with evidence link

---

## Summary: Top 10 Don'ts

1. ❌ Execute new build/deploy without explicit user instruction (Slice 1 DONE, Slice 2A awaiting approval)
2. ❌ Run gcloud without `--project` flag
3. ❌ Create resources in wrong GCP project
4. ❌ Recreate secrets or service accounts (they're DONE)
5. ❌ Expose secret values anywhere
6. ❌ Write to legacy workspace without LEGACY_WRITE_OK
7. ❌ Commit to legacy repo (ai-os) without permission
8. ❌ Deploy to PROD before DEV validation
9. ❌ Use Drive as SSOT (repo is truth now)
10. ❌ Assume facts not in documentation
