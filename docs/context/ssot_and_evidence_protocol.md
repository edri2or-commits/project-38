# SSOT and Evidence Protocol — Project 38 V2

**Last Updated:** 2025-12-15  
**Status:** ACTIVE (Drive-free operational model)

---

## Overview: Repo-Centric Truth

**Core Principle:** The repository is the Single Source of Truth (SSOT). All state, decisions, documentation, and evidence manifests live in the repo. External Drive is DEPRECATED.

**Why This Change:**
- **Drift prevention:** No sync lag between repo and external docs
- **Git-native workflow:** All changes tracked, reviewable, revertable
- **Session continuity:** New sessions start from repo state, not memory
- **Evidence integrity:** SHA256 hashes verify artifact authenticity

---

## What Lives Where

### IN REPO (Committed to Git)

#### 1. Source of Truth Documents
**Location:** `docs/context/`

- `project_facts.md` — Immutable facts (GCP projects, repos, paths)
- `operating_rules.md` — Operational protocols and anti-chaos rules
- `gcp_state_snapshot.md` — Current GCP resource state
- `phase_status.md` — Current phase/slice status
- `ssot_and_evidence_protocol.md` — This document

#### 2. Planning Documents
**Location:** `docs/phase-N/`

- Decision records (DR-XXX format)
- Architecture documents
- Phase plans and slice breakdowns

#### 3. Execution Artifacts
**Location:** `docs/phase-N/`

- Runbooks (step-by-step execution plans)
- Rollback plans (how to undo changes)
- Evidence pack templates (what to capture)

#### 4. Execution Logs (Excerpts Only)
**Location:** `docs/phase-N/`

- **Format:** `slice-XX_execution_log.md`
- **Content:** Summary + key commands + redacted outputs
- **Evidence:** Links to external evidence store via manifest
- **Rule:** Never commit RAW full logs (can be >100KB)

#### 5. Evidence Manifests
**Location:** `docs/evidence/manifest.md`

- **Content:** SHA256 hashes + paths to external evidence files
- **Purpose:** Verify integrity without committing large artifacts
- **Format:** Markdown table or JSON (see below)

#### 6. Traceability Matrix
**Location:** `docs/traceability_matrix.md`

- **Content:** Component status, evidence links, decision log
- **Purpose:** Cross-reference all work with evidence

---

### OUT OF REPO (External Evidence Store)

#### Location
**Base Path:** `C:\Users\edri2\project_38__evidence_store\`

**Structure:**
```
project_38__evidence_store/
├── phase-1/
│   ├── gate-a-analysis.md
│   └── patterns-extracted.md
├── phase-2/
│   ├── slice-01/
│   │   ├── raw_gcloud_outputs.txt
│   │   ├── docker_install_log.txt
│   │   └── vm_validation_screenshots/
│   ├── slice-02a/
│   │   ├── compose_up_output.txt
│   │   ├── n8n_initial_logs.txt
│   │   └── postgres_init_log.txt
│   └── slice-02b/
│       └── [kernel deployment evidence]
└── misc/
    └── [ad-hoc validation artifacts]
```

#### What Goes Here
- **RAW command outputs** (full stdout/stderr, before redaction)
- **Large logs** (Docker logs, Cloud Logging exports)
- **Screenshots** (GCP Console, n8n UI, etc.)
- **Binary artifacts** (tarballs, container images, DB dumps)
- **Sensitive artifacts** (even if redacted, keep originals separate)

#### Access Rules
- **Read:** Always available for reference
- **Write:** Only during execution phases (Slice N)
- **Commit:** NEVER commit this folder to Git
- **Share:** Never share full paths or contents in chat (use manifest references only)

---

## Evidence Manifest Format

### Location
**File:** `docs/evidence/manifest.md`

### Structure (Markdown Table)
```markdown
# Evidence Manifest — Project 38 V2

**Evidence Store Base:** `C:\Users\edri2\project_38__evidence_store\`

**Last Updated:** YYYY-MM-DD HH:MM UTC

---

| Slice | Artifact Name | Relative Path | Created (UTC) | SHA256 | Size | Description |
|-------|---------------|---------------|---------------|--------|------|-------------|
| 01 | VM creation output | phase-2/slice-01/raw_gcloud_outputs.txt | 2025-12-15 10:23 | abc123... | 45KB | Full gcloud compute instances create output |
| 01 | Docker install log | phase-2/slice-01/docker_install_log.txt | 2025-12-15 10:28 | def456... | 23KB | Docker Engine + Compose installation log |
| 01 | Firewall validation | phase-2/slice-01/firewall_rules.txt | 2025-12-15 10:30 | ghi789... | 3KB | gcloud compute firewall-rules list output |
| 02A | Compose up output | phase-2/slice-02a/compose_up_output.txt | 2025-12-15 11:15 | jkl012... | 12KB | Docker Compose up -d full output |
| 02A | N8N initial logs | phase-2/slice-02a/n8n_initial_logs.txt | 2025-12-15 11:16 | mno345... | 8KB | First 100 lines of n8n container logs |
```

### Verification Workflow
1. **During execution:** Generate evidence files in evidence store
2. **After execution:** Calculate SHA256 for each file
3. **Update manifest:** Add new entries with hash, size, timestamp
4. **Commit manifest:** Push manifest.md to repo (NOT the files themselves)
5. **Verify later:** Recalculate SHA256 to ensure integrity

### Example: Verify Evidence Integrity
```bash
# Calculate SHA256 of an evidence file
sha256sum C:\Users\edri2\project_38__evidence_store\phase-2\slice-01\raw_gcloud_outputs.txt

# Compare with manifest entry
# If hashes match → file is authentic and unchanged
# If hashes differ → file corrupted or tampered
```

---

## Session Start Protocol (Replaces Drive SSOT)

### Old Model (DEPRECATED)
- Sessions started with Drive paste (02_STATE.md, TOOLS.md, etc.)
- High risk of drift (Drive vs repo vs memory)
- Manual sync required after every session

### New Model (ACTIVE)
Every new session starts with:

**Step 1:** Read Session Start Packet  
**File:** `docs/context/session_start_packet.md`

**Step 2:** Print Snapshot (5-8 lines)  
Shows current phase, DONE items, NEXT steps

**Step 3:** Read Core SSOT Files  
- `docs/context/project_facts.md`
- `docs/context/operating_rules.md`
- `docs/traceability_matrix.md`

**Step 4:** Verify Key Hashes  
Compare hashes in session start packet with actual files

**Step 5:** Await Explicit Instruction  
No actions until user says "Execute Slice X" or similar

---

## Drive Deprecation Details

### What Changed
| Before (Drive-Based) | After (Repo-Based) |
|----------------------|-------------------|
| 02_STATE.md in Drive | `gcp_state_snapshot.md` + `phase_status.md` in repo |
| TOOLS.md in Drive | `operating_rules.md` + `session_start_packet.md` in repo |
| 01_ENTRY.md in Drive | `session_start_packet.md` in repo |
| 03_END_OF_CHAT_PROMPT.md in Drive | `evidence_pack_template.md` per slice in repo |
| Manual sync after each session | Git commit workflow (atomic updates) |

### Migration Status
- ✅ **Repo-based SSOT:** Fully implemented (this protocol)
- ✅ **Evidence store:** Created at `C:\Users\edri2\project_38__evidence_store\`
- ✅ **Evidence manifest:** Template created in `docs/evidence/manifest.md`
- ✅ **Session start packet:** Created in `docs/context/session_start_packet.md`
- ⏸️ **Drive archive:** User decides whether to keep for historical reference

### Transition Rules
1. **For new sessions:** Use `session_start_packet.md` (repo)
2. **For old sessions:** If user pastes Drive docs, acknowledge but redirect to repo
3. **For conflicts:** Repo takes precedence over Drive
4. **For evidence:** Always use manifest + external store (never commit large files)

---

## Anti-Patterns to Avoid

### ❌ Don't Do This
1. **Commit large evidence files** (>10KB) directly to repo
   - Use evidence store + manifest instead
2. **Assume Drive is up-to-date**
   - Drive is deprecated; repo is truth
3. **Create evidence artifacts without manifest entries**
   - Every evidence file needs manifest entry + SHA256
4. **Skip SHA256 verification**
   - Always verify hashes before trusting evidence
5. **Store secrets in evidence store**
   - Even redacted secrets should be handled carefully
   - Use `[REDACTED]` in logs, never paste actual values

### ✅ Do This Instead
1. **Commit small excerpts** (<10KB) with redaction to repo
2. **Link to external evidence** via manifest for large artifacts
3. **Update manifest atomically** with evidence generation
4. **Verify SHA256** before using evidence in decisions
5. **Keep secrets out of evidence** entirely (metadata only)

---

## Benefits of This Approach

### For Users
- **No Drive sync lag:** Repo is always current
- **Git history:** Full audit trail of all changes
- **Easy rollback:** `git revert` to undo bad changes
- **Session continuity:** New Claude instances start from same truth

### For Claude
- **Clear SSOT:** No ambiguity about current state
- **Evidence verification:** SHA256 ensures integrity
- **No Drive access required:** All info in repo
- **Minimal paste overhead:** Session start packet is 10-20 lines

### For Project Health
- **Drift prevention:** Repo + evidence store = single truth
- **Evidence integrity:** SHA256 hashes prevent tampering
- **Scalability:** Can handle 100+ slices without Drive limits
- **Portability:** Repo + evidence store can be cloned/moved

---

## Update Workflow (Replacing Drive Updates)

### Old Workflow (Drive)
1. User requests Drive update
2. Claude generates update request file
3. User manually updates Drive
4. Repo out of sync until next commit

### New Workflow (Repo-Only)
1. User requests update to SSOT
2. Claude updates relevant files in `docs/`
3. Claude commits changes to repo
4. Evidence manifest updated if new artifacts
5. Done — repo is immediately current

### Example: Update Phase Status
```bash
# Edit phase_status.md
# Update traceability_matrix.md
# Commit changes
git add docs/context/phase_status.md docs/traceability_matrix.md
git commit -m "chore: update phase status after Slice 2A completion"
git push origin main
```

---

## Summary: Key Rules

1. **Repo = SSOT** (not Drive)
2. **Evidence = External Store** (not repo)
3. **Manifest = Bridge** (SHA256 hashes link repo to evidence)
4. **Session Start = Packet** (not Drive paste)
5. **No Large Files in Repo** (<10KB limit for committed logs)
6. **SHA256 Always** (verify evidence integrity)
7. **No Secrets in Evidence** (metadata only)

---

## Questions & Troubleshooting

### Q: What if evidence store is lost?
**A:** Evidence manifest has SHA256 hashes. If hashes don't match after restore, evidence is invalid. Create new evidence by re-running slice (if possible) or mark as LOST in manifest.

### Q: Can I commit small evidence excerpts to repo?
**A:** Yes, if <10KB and properly redacted. For full logs, use evidence store + manifest.

### Q: What if repo and evidence store are out of sync?
**A:** Manifest is source of truth. If file missing from evidence store but in manifest, mark as MISSING. If file exists but not in manifest, add manifest entry.

### Q: How do I share evidence with others?
**A:** Share manifest + repo. Others can verify SHA256 hashes. If they need full artifacts, provide evidence store separately (with secret redaction).

### Q: What if I need to update old evidence?
**A:** Never modify original evidence files. Create new version in evidence store with new timestamp + SHA256. Update manifest with "v2" entry.

---

## Status: ACTIVE

This protocol is ACTIVE as of 2025-12-15. All future sessions use repo-based SSOT + evidence store.

Drive is DEPRECATED for operational use (may be kept for historical reference).
