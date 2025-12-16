# Project 38 V2

**Production-Grade AI Automation Platform**

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
- **Slice:** Slice 1 ✅ DONE (VM baseline), Slice 2A 📋 PLANNED (N8N deployment)
- **Environment:** DEV (`project-38-ai`)

### Key Links
- [Strategic Narrative](PROJECT_NARRATIVE.md) — Start here (entry point)
- [Traceability Matrix](docs/traceability_matrix.md) — Current status dashboard
- [Operating Rules](docs/context/operating_rules.md) — How we operate
- [Session Start Packet](docs/context/session_start_packet.md) — For new Claude sessions

### Documentation Structure
```
project-38/
├── PROJECT_NARRATIVE.md          ← YOU ARE HERE (entry point)
├── README.md                     ← Quick links (this file)
├── docs/
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
- Duration: 20-30 minutes (estimated)
- Approval: User must say **"Execute Slice 2A"**
- Documentation: [Runbook](docs/phase-2/slice-02a_runbook.md) | [Evidence Pack](docs/phase-2/slice-02a_evidence_pack.md) | [Rollback Plan](docs/phase-2/slice-02a_rollback_plan.md)

---

**Questions?** Read [PROJECT_NARRATIVE.md](PROJECT_NARRATIVE.md) first — it answers most of them.

---

*Last Updated: 2025-12-16*