# Evidence Manifest — Project 38 V2

**Evidence Store Base Path:** `C:\Users\edri2\project_38__evidence_store\`  
**Last Updated:** 2025-12-16 (Evidence store populated)  
**Purpose:** Track external evidence artifacts with SHA256 integrity verification

---

## How to Use This Manifest

### Adding New Evidence
1. Generate evidence file during slice execution
2. Save to evidence store: `C:\Users\edri2\project_38__evidence_store\phase-2\slice-XX\filename.txt`
3. Calculate SHA256 hash:
   ```bash
   # Windows PowerShell
   Get-FileHash -Path "C:\Users\edri2\project_38__evidence_store\phase-2\slice-XX\filename.txt" -Algorithm SHA256
   
   # Linux/Mac/WSL
   sha256sum C:\Users\edri2\project_38__evidence_store\phase-2\slice-XX\filename.txt
   ```
4. Add row to manifest table below
5. Commit manifest to repo (NOT the evidence file itself)

### Verifying Evidence
1. Locate evidence file using relative path from manifest
2. Recalculate SHA256 hash
3. Compare with manifest hash
4. If match → Evidence is authentic
5. If mismatch → Evidence corrupted or tampered (investigate)

---

## Manifest Table

| Slice | Artifact Name | Relative Path | Created (UTC) | SHA256 | Size | Description |
|-------|---------------|---------------|---------------|--------|------|-------------|
| 01 | VM creation output | phase-2/slice-01/vm_create_raw.txt | 2025-12-15 10:23:00 | CECBB7CFFCBA3490B7BA5977268AF83821A50590702CF6CC58BF116B971994CD | 2107 | Full gcloud compute instances create command output |
| 01 | Docker install log | phase-2/slice-01/docker_install.txt | 2025-12-15 10:28:00 | 84C31E641E9D8323EF62C38129CDB82FE5DD007C35D503B0DAC8E0B1411A1CAE | 9351 | Docker Engine + Compose installation full log |
| 01 | Firewall rules verification | phase-2/slice-01/firewall_verify.txt | 2025-12-15 10:30:00 | E3F8E79486E8AA98D5BB51F2ED1E94A39E0D347BF7F1437E97CD0C8962B02138 | 3905 | gcloud compute firewall-rules list output |
| 01 | IAM validation | phase-2/slice-01/iam_verify.txt | 2025-12-15 10:32:00 | 34676ADAA4D9447A94B3F6B9EC2E5F23DEAE00F766B66B75B159D3E0B4090B20 | 5644 | Service account impersonation test results |

**Note:** Evidence store created 2025-12-16. All artifacts include SHA256 hashes for integrity verification. All secrets redacted.

---

## Evidence Store Structure

**Recommended directory layout:**

```
C:\Users\edri2\project_38__evidence_store\
├── README.md                          # Evidence store documentation
├── phase-1/
│   ├── gate-a-analysis.md             # Gate A decision analysis
│   └── patterns-extracted.md          # AIOS V1 patterns extraction
├── phase-2/
│   ├── slice-01/
│   │   ├── vm_create_raw.txt          # Raw gcloud VM creation output
│   │   ├── docker_install.txt         # Docker installation log
│   │   ├── firewall_verify.txt        # Firewall rules verification
│   │   ├── iam_verify.txt             # IAM validation results
│   │   └── screenshots/               # Optional: GCP Console screenshots
│   ├── slice-02a/
│   │   ├── compose_up_output.txt      # Docker Compose up full output
│   │   ├── n8n_initial_logs.txt       # N8N container startup logs
│   │   ├── postgres_init_log.txt      # PostgreSQL initialization log
│   │   ├── secret_injection_test.txt  # Secret access validation results
│   │   └── port_forward_test.txt      # SSH port-forward connectivity test
│   ├── slice-02b/
│   │   ├── kernel_deploy_output.txt   # Kernel deployment full log
│   │   ├── kernel_health_check.txt    # Kernel service health validation
│   │   └── api_integration_test.txt   # LLM API connectivity tests
│   └── slice-03/
│       ├── smoke_test_results.txt     # End-to-end smoke test outputs
│       └── validation_report.md       # Slice 3 validation summary
└── misc/
    ├── troubleshooting/               # Ad-hoc debugging artifacts
    └── performance-baselines/         # Performance measurement data
```

---

## Integrity Verification Examples

### Example 1: Verify Slice 01 VM Creation Output
```bash
# Calculate current hash
Get-FileHash -Path "C:\Users\edri2\project_38__evidence_store\phase-2\slice-01\vm_create_raw.txt" -Algorithm SHA256

# Compare with manifest entry
# Manifest shows: ABC123DEF456...
# Calculated shows: ABC123DEF456...
# Result: ✅ MATCH → Evidence authentic
```

### Example 2: Hash Mismatch (Corruption Detected)
```bash
# Calculate current hash
Get-FileHash -Path "C:\Users\edri2\project_38__evidence_store\phase-2\slice-02a\compose_up_output.txt" -Algorithm SHA256

# Compare with manifest entry
# Manifest shows: XYZ789ABC123...
# Calculated shows: ABC999DEF111...
# Result: ❌ MISMATCH → Evidence corrupted or tampered
# Action: Investigate or re-generate evidence
```

---

## Security & Redaction Rules

### What to Store in Evidence Store
✅ **Safe to store:**
- Command outputs with `[REDACTED]` replacements for secrets
- Logs with timestamps, service names, resource IDs
- GCP Console screenshots (with secret fields blurred/redacted)
- Binary artifacts (container images, DB dumps) — properly encrypted if sensitive

❌ **NEVER store:**
- Raw secret values (API keys, passwords, tokens)
- Unredacted credentials
- Private keys or certificates
- PII (personally identifiable information) without consent

### Redaction Best Practices
When saving evidence to store:
1. Replace secret values with `[REDACTED]`
2. Keep structure intact (e.g., `secret_value: [REDACTED]`, not just `[REDACTED]`)
3. Include metadata (secret name, version, timestamp)
4. Example:
   ```
   # Original (DO NOT STORE)
   ANTHROPIC_API_KEY=sk-ant-abc123def456...
   
   # Redacted (OK TO STORE)
   ANTHROPIC_API_KEY=[REDACTED]
   # Secret name: anthropic-api-key
   # Version: 2
   # Accessed at: 2025-12-15 10:45:00 UTC
   ```

---

## Evidence Lifecycle

### Creation
1. Execute slice step
2. Capture output to file in evidence store
3. Redact sensitive values
4. Calculate SHA256 hash
5. Add manifest entry
6. Commit manifest to repo

### Verification
1. Read manifest entry
2. Locate evidence file
3. Recalculate SHA256
4. Compare hashes
5. If match → Use evidence
6. If mismatch → Flag corruption

### Update/Version
1. **Never modify original evidence files**
2. Create new version: `filename_v2.txt`
3. Calculate new SHA256
4. Add new manifest entry (mark as v2)
5. Keep original entry for audit trail

### Deletion
1. Remove file from evidence store
2. Update manifest: change hash to `DELETED`, add deletion timestamp
3. Keep manifest entry for audit trail (don't delete row)
4. Example:
   ```
   | 01 | VM creation output | phase-2/slice-01/vm_create_raw.txt | 2025-12-15 10:23:00 | DELETED (2025-12-20) | 0KB | Removed after 30-day retention |
   ```

---

## Retention Policy

**Recommendation:**
- **Phase 1-2 evidence:** Keep indefinitely (foundational decisions)
- **Slice execution logs:** Keep for 90 days after slice completion
- **Troubleshooting artifacts:** Keep for 30 days after resolution
- **Performance baselines:** Keep indefinitely (comparison reference)

**User decides final retention policy.**

---

## Missing Evidence

If evidence file is missing but manifest entry exists:

### Mark as MISSING
```
| 02A | N8N logs | phase-2/slice-02a/n8n_initial_logs.txt | 2025-12-15 11:16:00 | MISSING (noted 2025-12-20) | 0KB | File lost, re-run slice to regenerate |
```

### Re-generate if Possible
1. Re-run slice step (if idempotent)
2. Capture new evidence
3. Calculate new SHA256
4. Update manifest entry (mark as v2, regenerated)

### Accept Loss if Not Critical
1. Update manifest with MISSING status
2. Document impact (e.g., "Evidence lost, but slice completed successfully")
3. Continue with project

---

## Cross-Reference with Repo

### Execution Logs (in Repo)
**Location:** `docs/phase-2/slice-XX_execution_log.md`

**Content:** 
- Summary of slice execution
- Key commands (copy-paste ready)
- Redacted outputs (<10KB)
- **Links to evidence store:** "See full output at `phase-2/slice-XX/filename.txt` (SHA256: abc123...)"

### Evidence Manifest (in Repo)
**Location:** `docs/evidence/manifest.md` (this file)

**Content:**
- SHA256 hashes + paths to external evidence
- Integrity verification mechanism
- Audit trail for evidence lifecycle

---

## Summary: Key Rules

1. **Evidence store is external** (not committed to repo)
2. **Manifest is committed** (tracks evidence with SHA256)
3. **SHA256 always** (verify integrity before using evidence)
4. **Redact secrets** (never store raw values)
5. **Never modify originals** (create versions instead)
6. **Audit trail** (keep manifest entries even after deletion)
7. **Size limit** (commit <10KB excerpts to repo, full logs to store)

---

## Status: ACTIVE

This manifest is ACTIVE as of 2025-12-15.

**Next actions:**
- Migrate Slice 1 evidence to evidence store
- Calculate SHA256 hashes for migrated files
- Update PLACEHOLDER entries above with actual hashes
- Create evidence store README.md with usage instructions
