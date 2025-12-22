# Operating Rules — Project 38 (V2)

**Last Updated:** 2025-12-22  
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

## Rule 12: GitHub Autonomy (FULL ACCESS)

**Status:** Claude has FULL autonomous access to GitHub operations.

### Available Tools

Claude has 2 independent methods to interact with GitHub:

#### Method 1: GitHub MCP Tool (Preferred for Multi-File Operations)
**Tool Name:** `github:push_files`

**Capabilities:**
- ✅ Push multiple files in a single atomic commit
- ✅ Create/update/delete files on any branch
- ✅ Automatic commit with custom message
- ✅ Direct push to main (no PR required)
- ✅ Full file content manipulation

**Example:**
```javascript
github:push_files({
  branch: "main",
  owner: "edri2or-commits",
  repo: "project-38",
  message: "Fix: Update documentation",
  files: [
    {path: "README.md", content: "..."},
    {path: "docs/file.md", content: "..."}
  ]
})
```

**Other GitHub MCP Tools:**
- `github:create_or_update_file` - Single file operations
- `github:create_pull_request` - For review workflows
- `github:create_branch` - Branch management
- All read operations (get_file_contents, list_commits, etc.)

#### Method 2: Desktop Commander + Git CLI (Alternative)
**Tool Name:** `Desktop Commander:start_process`

**Capabilities:**
- ✅ Full git command-line access
- ✅ Local repository operations
- ✅ Complex git workflows (rebase, cherry-pick, etc.)
- ✅ Direct shell access to git

**Example:**
```bash
cd C:\Users\edri2\project_38
git add .
git commit -m "Fix: Update documentation"
git push origin main
```

### Operating Model

**Claude's Authority:**
- ✅ Claude can prepare all changes (fixes, updates, new files)
- ✅ Claude can stage all changes locally
- ✅ Claude can create commit messages
- ✅ Claude requests user approval ONLY for: `git push` or GitHub MCP push operations
- ✅ After approval, Claude executes the push immediately

**User Approval Required For:**
1. **Git Push** - Pushing commits to GitHub
2. **PR Creation** - Creating pull requests (if needed)
3. **Branch Operations** - Creating/deleting branches (if non-standard)

**User Approval NOT Required For:**
- File modifications (local)
- Documentation updates (local)
- Code fixes (local)
- Git staging/committing (local)
- Reading GitHub content
- Analyzing repository state

### Decision Tree: When to Use Each Method

**Use GitHub MCP (push_files) when:**
- ✅ Updating 1-10 files simultaneously
- ✅ Need atomic commit (all or nothing)
- ✅ Simple, straightforward file updates
- ✅ Don't need complex git operations
- ✅ Want cleaner tool call syntax

**Use Desktop Commander + Git CLI when:**
- ✅ Complex git operations (rebase, merge, cherry-pick)
- ✅ Need to see git diff before push
- ✅ Working with git history
- ✅ Need granular control over staging
- ✅ Debugging git issues

### Approval Protocol

**Standard Workflow:**
1. User requests change (e.g., "fix fetch_secrets.sh scope issue")
2. Claude analyzes and prepares fixes
3. Claude shows summary of changes
4. Claude asks: "Push to GitHub?" (yes/no/modify)
5. User approves with "yes" or "כן"
6. Claude executes push using chosen method
7. Claude confirms with commit SHA

**Example Dialogue:**
```
User: תקן את fetch_secrets.sh
Claude: [analyzes, creates fix]
        מוכן לדחוף ל-GitHub:
        - fetch_secrets.sh: הוספת scope parameter
        Commit: "Fix: Add scope parameter to fetch_secrets"
        אישור? (כן/לא)
User: כן
Claude: [pushes to GitHub]
        ✅ Pushed: commit b82c688
```

### What Claude Documents

**After Every Push:**
Claude must create a session log entry in:
- **Location:** `docs/sessions/YYYY-MM-DD_session_brief.md`

**Required Contents:**
1. **Date/Time:** ISO 8601 timestamp
2. **Action:** What was done (e.g., "Fixed 4 files + pushed to GitHub")
3. **Files Changed:** List with brief description
4. **Commit SHA:** GitHub commit ID
5. **Rationale:** Why each change was made
6. **Impact:** What this fixes or enables

**Example Log Entry:**
```markdown
## 2025-12-16 10:30 UTC - GitHub Repo Fixes

**Action:** Fixed 4 critical issues + pushed to GitHub

**Files Changed:**
1. fetch_secrets.sh - Added scope parameter (n8n|kernel|all)
2. startup.sh - Removed apt-get upgrade (timeout prevention)
3. README.md - Removed duration estimate
4. docs/context/phase_status.md - Updated to Slice 1 DONE

**Commit:** b82c6889a107d6e08a3640c516ef0fa05d3e2da6
**Link:** https://github.com/edri2or-commits/project-38/commit/b82c688

**Rationale:**
- fetch_secrets.sh: n8n-runtime SA only has access to 3 secrets, not 7
- startup.sh: Documented timeout issues in Slice 1 execution
- README.md: User decision to remove time estimates from SoT
- phase_status.md: Sync with actual state (Slice 1 complete)

**Impact:**
- ✅ Slice 2A will now work (scope fix critical)
- ✅ VM startup more reliable (no timeout)
- ✅ Documentation accurate (reflects reality)
```

### Session Logs Directory Structure
```
docs/sessions/
├── 2025-12-15_session_brief.md  (Slice 1 execution)
├── 2025-12-16_session_brief.md  (Today's fixes)
└── README.md                     (Index of all sessions)
```

### Security Notes

**Claude Never:**
- ❌ Pushes secret values to GitHub
- ❌ Commits sensitive credentials
- ❌ Pushes to wrong repository
- ❌ Pushes without user approval for final push operation
- ❌ Modifies git history without explicit instruction

**Claude Always:**
- ✅ Redacts secrets before any git operation
- ✅ Verifies repository URL before push
- ✅ Uses correct branch (usually main)
- ✅ Provides clear commit messages
- ✅ Documents all pushes in session logs

---

## Rule 13: Gate IDs Naming Convention

**Purpose:** Prevent ambiguity when referencing verification gates across different contexts.

### Format
```
<namespace>-Gate-<number>
```

### Namespace Examples

**POC-level Gates:**
- `POC-01-Gate-1` - Headless activation verification
- `POC-02-Gate-3` - Telegram webhook response validation
- `POC-03-Gate-2` - Mock Kernel webhook test

**Document/Issue-level Gates:**
- `DS-Gate-3` - Deterministic Secret (networks verified)
- `LCS-Gate-A` - Local Compose Secret (no warnings)
- `LCS-Gate-B.2` - Postgres logs validation

**Phase-level Gates:**
- `Phase1-Gate-A` - VM vs Cloud Run decision
- `Slice01-Gate-1` - VM creation success

### Usage Rules

**✅ CORRECT:**
```
POC-03-Gate-2 PASS - Mock Kernel responded with HTTP 200
```

**❌ WRONG:**
```
Gate 2 PASS  (missing namespace - ambiguous)
```

### When Multiple Gates Exist

If you encounter "Gate 3" without namespace:
1. **STOP** before claiming which gate
2. **Provide 2 concrete examples** from SSOT:
   - Example: "DS-Gate-3 = networks, POC-02-Gate-3 = webhook"
3. **Ask for mapping confirmation** if uncertain:
   ```
   רציתי לאמת: האם זה POC-03-Gate-3 או LCS-Gate-3?
   ```

### Grep for Mapping (If Needed)

**PowerShell:**
```powershell
Get-ChildItem -Path docs -Recurse -Filter *.md | 
  Select-String "Gate.*3" | 
  Select-Object -First 10 -Property @{Name='Location';Expression={"$($_.Path):$($_.LineNumber)"}}
```

**Do NOT run `grep docs/**/*.md`** (globstar issues + prints content)

### Documentation Standard

**When documenting new gates:**
1. Always include namespace in initial definition
2. Use consistent format: `NAMESPACE-Gate-N`
3. Add to section header or summary

**Example:**
```markdown
## POC-03 Verification Gates

### POC-03-Gate-1: Webhook Configuration
- Check: httpMethod, path, responseMode
- Expected: POST, mock-kernel, lastNode

### POC-03-Gate-2: Webhook Response
- Check: HTTP status + JSON structure
- Expected: 200 OK + {"response":...,"status":"success"}
```

---

## Rule 14: Doc-sprawl Gate (HARD RULE)

### No New Files Without Registry

**Every new documentation file MUST:**

1. ✅ Check if existing file can hold the content
2. ✅ Update `docs/_system/_registry.yml` BEFORE creation
3. ✅ Update `docs/_system/SYSTEM_MAP.md` if structural change
4. ✅ Comment in Control Room Issue (#24) if decision-related

**Forbidden:**
❌ Create "orphan" docs (files not linked from SYSTEM_MAP or registry)  
❌ Duplicate content across multiple files  
❌ Create temporary docs in `docs/` (use `/tmp/` instead)

**Registry Structure:**
```yaml
canon_files:
  - path: docs/context/new_file.md
    purpose: Brief description
    created: YYYY-MM-DD
    category: canon|secondary|evidence
```

**Enforcement:**
- Claude asks: "Does existing file exist for this?" before creating
- Claude updates registry entry BEFORE file creation
- Claude comments in Issue #24 if decision doc

**Evidence:** See `docs/_system/_registry.yml` for file inventory

---

## Rule 15: Control Room Authority (SSOT)

### Issue #24 = State Authority

**Authority Hierarchy:**

1. **PRIMARY (State Authority):**  
   - **Control Room Issue #24** ← All decisions, gates, deployments tracked here
   - Link: https://github.com/edri2or-commits/project-38/issues/24

2. **NAVIGATION (Map):**  
   - **SYSTEM_MAP.md** ← Complete navigation hub
   - Link: docs/_system/SYSTEM_MAP.md

3. **SNAPSHOTS (Derived):**  
   - phase_status.md ← Current phase/slice/gates
   - traceability_matrix.md ← Component status dashboard
   - README.md ← Quick reference
   - PROJECT_NARRATIVE.md ← Strategic context

**Rule:** If Control Room Issue #24 says one thing and other docs say another → **Issue #24 wins.**

### Protocol (5 מצוות)

**ALWAYS post to Control Room Issue (#24) for:**

1. ✅ **Strategic decisions** (architecture, approach, direction)
2. ✅ **Gate closures** (with evidence link)
3. ✅ **Deployments** (before: plan, after: evidence)
4. ✅ **New documentation** (why created, where located)
5. ❌ **No scattered chats** (single conversation thread)

**Example Comment Structure:**
```markdown
## [Action Type] - [Brief Title]

**What:** [1-2 sentence description]
**Why:** [Rationale]
**Evidence:** [Link to docs/evidence/YYYY-MM-DD_*.txt]
**Impact:** [What this changes]

[Additional details if needed]
```

**Benefits:**
- ✅ Single source of decisions (no searching)
- ✅ GitHub notifications (mobile-friendly)
- ✅ Audit trail (GitHub timestamps + user attribution)
- ✅ "Chat אחד" protocol ready (Stage 1: manual sync)

**Claude's Responsibility:**
- Post summaries to #24 after significant actions
- Link evidence files from #24 comments
- Keep #24 current (latest status always visible)

---

## Rule 16: Evidence-First Protocol (IssueOps)

**החל מיידית:** כל טענה/החלטה/סגירת Gate = 3 הוכחות חובה, בפוסט ב-Issue #24 (SSOT).

### 1) PR/Commit Proof (חובה)
- PR: <url>
- SHA: <sha>
- מצב: merged/open

### 2) E2E Execution Proof (חובה)
- Workflow Run: <url>
- Trigger: issue_comment.created (Issue #24)
- Status: success/failed + duration

> `issue_comment` הוא event רשמי עם activity types כמו created/edited/deleted.

### 3) Code Diff Proof (חובה)
2–5 שורות diff שמראות את הדבר עצמו (guard/permissions/קריאת payload).

### "אני רואה משהו אחר" — אין בקשות אימות ידני

**❌ לא להגיד:** "תרענן / תבדוק בעצמך"

**✅ במקום זה:** לאמת דרך API ולהדביק פלט/לינקים

**דוגמאות אימות (מותר להדביק פלט מלא):**
```bash
# אימות תוכן קובץ מ-branch
gh api repos/edri2or-commits/project-38/contents/FILE?ref=BRANCH

# אימות סטטוס PR
gh pr view NUM --json state,mergedAt,commits

# אימות workflow run + לוגים
gh run view RUN_ID --log
```

### Security Baseline

**קריאת Event Data:**
- **רק מ-`GITHUB_EVENT_PATH`** (payload מלא של webhook)
- `GITHUB_EVENT_PATH` מכיל JSON של כל ה-webhook event
- דוגמה: `jq -r '.comment.body' "$GITHUB_EVENT_PATH"`

**הרשאות:**
- שימוש ב-`GITHUB_TOKEN` עם מינימום הרשאות (least privilege)
- דוגמה: `permissions: { issues: write, contents: read }`

**אסור:**
- ❌ קריאת user input דרך `${{ github.event.comment.body }}` ישירות ל-bash
- ❌ שימוש ב-heredoc עם untrusted input
- ❌ string interpolation של תוכן משתמש

**מותר:**
- ✅ `jq` או `json.load()` עם `GITHUB_EVENT_PATH`
- ✅ הרשאות מפורשות בראש workflow
- ✅ access control guards (OWNER/MEMBER בלבד)

---

## Summary: Top 12 Don'ts

1. ❌ Execute new build/deploy without explicit user instruction
2. ❌ Run gcloud without `--project` flag
3. ❌ Create resources in wrong GCP project
4. ❌ Recreate secrets or service accounts (they're DONE)
5. ❌ Expose secret values anywhere
6. ❌ Write to legacy workspace without LEGACY_WRITE_OK
7. ❌ Commit to legacy repo (ai-os) without permission
8. ❌ Deploy to PROD before DEV validation
9. ❌ Use Drive as SSOT (repo is truth now)
10. ❌ Assume facts not in documentation
11. ❌ Use "Gate N" without namespace (use "NAMESPACE-Gate-N")
12. ❌ Say "check yourself" or "refresh" — validate via API instead
