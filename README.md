# Project 38 V2

**Production-Grade AI Automation Platform**

---

## 🎯 Control Room

**→ [Issue #24 — Control Room (Chat & State Authority)](https://github.com/edri2or-commits/project-38/issues/24) ←**

**Current State:** All decisions, gates, and deployments tracked here  
**Navigation:** [SYSTEM_MAP.md](docs/_system/SYSTEM_MAP.md) — Complete project navigation

---

## 🚀 Start Here

**New to the project?** Read this first:

### → [**PROJECT_NARRATIVE.md**](PROJECT_NARRATIVE.md) ←

**This is your entry point.** It explains:
- **Why** we're rebuilding (V1 pain points and lessons)
- **What** we're building (V2 vision and goals)
- **How** we're building it (architecture decisions)
- **Where** we are now (current state)
- **Operating model** (how to work with this project)

**Time to read:** 15-20 minutes  
**Worth it:** Absolutely.

---

## Quick Reference

### Current Status
- **Phase:** Phase 2 — Infrastructure & Deployment
- **Status:** Slice 2A ✅ DONE, POC-01 ✅ PASS, POC-02 ✅ PASS, Observability ✅ ACTIVE
- **Environment:** DEV (`project-38-ai`)

### Key Links
- **[Control Room (Issue #24)](https://github.com/edri2or-commits/project-38/issues/24)** — Chat & state authority
- **[SYSTEM_MAP.md](docs/_system/SYSTEM_MAP.md)** — Navigation hub (start here)
- [Strategic Narrative](PROJECT_NARRATIVE.md) — Why/What/How entry point
- [Traceability Matrix](docs/traceability_matrix.md) — Current status dashboard
- [Operating Rules](docs/context/operating_rules.md) — How we operate
- [Session Start Packet](docs/context/session_start_packet.md) — For new Claude sessions

### Documentation Structure
```
project-38/
├── PROJECT_NARRATIVE.md          ← Entry point (why/what/how)
├── README.md                     ← Quick links (this file)
├── docs/
│   ├── _system/                  ← Navigation and registry
│   │   ├── SYSTEM_MAP.md         ← Complete navigation hub
│   │   └── _registry.yml         ← File tracking (sprawl prevention)
│   ├── context/                  ← Source of truth (facts, rules, status)
│   ├── phase-1/                  ← Planning & analysis
│   ├── phase-2/                  ← Deployment artifacts
│   └── evidence/                 ← Evidence manifest (SHA256 hashes)
└── traceability_matrix.md        ← Component status + evidence links
```

---

## For New Claude Sessions

**Starting a new Claude session?**

1. Read [session_start_packet.md](docs/context/session_start_packet.md)
2. Copy-paste the template to Claude
3. Claude reads PROJECT_NARRATIVE.md + core files
4. Claude prints status snapshot
5. Ready to work!

---

## Core Principles

1. **GitOps-Native** — Every credential injected via Secret Manager, zero manual UI clicks
2. **Infrastructure-as-Evidence** — Every change documented with SHA256-verified evidence
3. **Least Privilege** — 3 service accounts, each with minimal required permissions
4. **Approval Gates** — No deployment without explicit "Execute Slice X" approval

---

## Repository Info

- **GitHub:** https://github.com/edri2or-commits/project-38
- **GCP DEV:** `project-38-ai`
- **GCP PROD:** `project-38-ai-prod` (mirror after DEV validation)
- **Primary Account:** edri2or@gmail.com

---

## What's Next?

**Slice 2A: N8N + Postgres Deployment**
- Status: 📋 PLANNED (documentation ready)
- Approval: User must say **"Execute Slice 2A"**
- Documentation: [Runbook](docs/phase-2/slice-02a_runbook.md) | [Evidence Pack](docs/phase-2/slice-02a_evidence_pack.md) | [Rollback Plan](docs/phase-2/slice-02a_rollback_plan.md)

---

**Questions?** Read [PROJECT_NARRATIVE.md](PROJECT_NARRATIVE.md) first — it answers most of them.

---

*Last Updated: 2025-12-21*
