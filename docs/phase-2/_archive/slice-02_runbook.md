# SUPERSEDED - Slice 2 Runbook (Original)

**Status:** ⚠️ SUPERSEDED BY slice-02a_runbook.md  
**Date Created:** 2025-12-15  
**Date Superseded:** 2025-12-15  
**Reason:** Split to Slice 2A (N8N only) + Slice 2B/3 (Kernel) for least privilege compliance

---

## Why This File Was Superseded

**Original Plan (Slice 2):**
- Deploy 3 services: Postgres + N8N + Kernel
- Use 7 secrets on single VM with n8n-runtime SA
- **Problem:** n8n-runtime SA has access to only 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token)
- **Problem:** Kernel needs 4 additional secrets (openai-api-key, anthropic-api-key, gemini-api-key, github-pat)
- **Problem:** Violates least privilege - n8n-runtime cannot access Kernel secrets

**Revised Plan (Slice 2A):**
- Deploy 2 services: Postgres + N8N only
- Use 3 secrets (n8n-encryption-key, postgres-password, telegram-bot-token)
- Access via SSH port-forward (no firewall changes)
- **Benefit:** Respects SA permission boundaries
- **Benefit:** Minimal scope (faster, safer)

**Deferred (Slice 2B/3):**
- Kernel deployment with 4 secrets
- Requires architectural decision:
  - Option 1: Separate VM with kernel-runtime SA
  - Option 2: Multi-SA approach
  - Option 3: Alternative credential mechanism

---

## Current Status

**Active Document:** `slice-02a_runbook.md`  
**This Document:** Archived for traceability only  
**Do Not Use:** This plan is no longer valid

---

## Original Content

This file originally contained a comprehensive runbook for deploying all 3 services (Postgres, N8N, Kernel) simultaneously. The full content has been archived but is not reproduced here to avoid confusion.

**Key differences from Slice 2A:**
- 3 services vs 2 services
- 7 secrets vs 3 secrets
- Direct :5678 access vs SSH port-forward
- Single-phase deployment vs phased deployment (2A + 2B/3)

---

**For current deployment instructions, see:** `slice-02a_runbook.md`
