# Repositories and Paths — Project 38 (V2)

**Generated:** 2024-12-15

---

## NEW Workspace (Project 38 V2)

### Primary Working Directory
**Path:** `C:\Users\edri2\project_38`

**Rules:**
- ✅ **WRITE ALLOWED** — This is the active workspace
- All new work, configs, and documentation go here
- Safe to create/modify files and folders

---

## NEW Repository (GitHub)

**URL:** https://github.com/edri2or-commits/project-38

**Rules:**
- This is the ONLY repo for Project 38 V2 work
- All commits, PRs, and changes should target this repo
- Connected to DEV (`project-38-ai`) and PROD (`project-38-ai-prod`) GCP projects

---

## LEGACY Workspace (AIOS V1)

### Quarantine Path
**Path:** `C:\Users\edri2\Desktop\AI\ai-os`

**Rules:**
- ⛔ **READ-ONLY by default**
- Reference-only unless user provides keyword: `LEGACY_WRITE_OK`
- Do NOT modify or write anything here without explicit permission
- Can perform read-only checks if needed (e.g., inspect old configs)

---

## LEGACY Repository (GitHub)

**URL:** https://github.com/edri2or-commits/ai-os

**Rules:**
- Reference-only, no changes unless user says `LEGACY_WRITE_OK`
- Historical context only
- Not connected to Project 38 infrastructure

---

## Google Account

**Primary Account:** edri2or@gmail.com

**Usage:**
- GCP authentication
- GitHub integration
- Drive access (when authorized)

---

## Safety Keywords

- **LEGACY_WRITE_OK** — User must explicitly provide this keyword to allow writes to legacy paths/repos
- Without this keyword: legacy is READ-ONLY

---

## Workspace Structure (NEW)

```
C:\Users\edri2\project_38\
├── docs/
│   ├── context/           ← Context snapshots (this file is here)
│   └── drive_updates/
│       └── pending/       ← Drive update requests (not auto-synced)
├── infra/                 ← Infrastructure configs (future)
├── workloads/            ← Service code (future)
└── .github/              ← CI/CD workflows (future)
```

---

## Repository Workflow

1. **Local changes** → `C:\Users\edri2\project_38`
2. **Commit & push** → `github.com/edri2or-commits/project-38`
3. **CI/CD triggers** → GitHub Actions → GCP (DEV or PROD)
4. **Legacy** → read-only unless `LEGACY_WRITE_OK` provided
