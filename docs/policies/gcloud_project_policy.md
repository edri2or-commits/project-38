# gcloud Project ID Policy — Project 38 V2

**Created:** 2025-12-16  
**Status:** ACTIVE  
**Purpose:** Prevent "runs on wrong project" errors by enforcing PROJECT_ID discipline

---

## 🚨 THE PROBLEM (RESOLVED)

**Before 2025-12-16:**
- gcloud default project was `edri2or-mcp`
- All scripts hardcoded `--project=project-38-ai` to work around drift
- Risk: Future commands without `--project` flag would operate on wrong project

**Resolution:**
- ✅ Default project changed to `project-38-ai` (2025-12-16)
- ✅ All deployment scripts already include explicit `--project` flag
- ✅ Policy document created

---

## ✅ MANDATORY RULES

### Rule 1: All Production Scripts MUST Include --project

```bash
# ✅ CORRECT
gcloud secrets versions access latest \
  --secret=postgres-password \
  --project=project-38-ai

# ❌ WRONG - relies on default
gcloud secrets versions access latest \
  --secret=postgres-password
```

### Rule 2: Default Project = project-38-ai

Current: `project-38-ai` ✅

If drift detected: `gcloud config set project project-38-ai`

### Rule 3: Documentation Examples

Always include `--project=project-38-ai` or add note about requirement

---

## 📋 AUDIT RESULTS (2025-12-16)

### deployment/n8n/load-secrets.sh
```bash
PROJECT_ID="project-38-ai"  # ✅ Hardcoded
# All 3 gcloud calls use --project=$PROJECT_ID
```
**Status:** ✅ COMPLIANT

### Documentation Files
- Some examples lack --project for readability (LOW RISK - examples only)

---

## 🔍 VERIFICATION

```bash
$ gcloud config get-value project
project-38-ai  # ✅ Expected
```

---

## 📝 INCIDENT LOG

### 2025-12-16: Default Project Drift
- **Issue:** Default was edri2or-mcp
- **Impact:** NONE (scripts had explicit --project)
- **Resolution:** gcloud config set project project-38-ai
- **Status:** RESOLVED
