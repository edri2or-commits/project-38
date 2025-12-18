# GitHub App — project-38-scribe

**Created:** 2025-12-18  
**Purpose:** Automated GitHub operations for Project 38

---

## Overview

`project-38-scribe` is a GitHub App that provides automated access to the `project-38` repository with specific permissions for CI/CD, documentation updates, and workflow management.

---

## Key Information

| Property | Value |
|----------|-------|
| **App Name** | project-38-scribe |
| **Created** | 2025-12-18 |
| **Homepage** | https://github.com/edri2or-commits/project-38 |
| **Installed On** | edri2or-commits/project-38 |
| **Private Key** | `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem` |
| **Webhook** | Disabled (not needed for current use case) |

---

## Permissions

See [permissions.md](permissions.md) for full details.

**Summary:**
- ✅ Actions: Read and write
- ✅ Contents: Read and write
- ✅ Workflows: Read and write
- ✅ Metadata: Read-only (automatic)

---

## Files in this Directory

- **README.md** (this file) — Overview and quick reference
- **setup.md** — Detailed setup instructions and history
- **permissions.md** — Permission matrix and use cases
- **usage.md** — How to use the App in automation

---

## Quick Links

- [Setup Documentation](setup.md)
- [Permission Details](permissions.md)
- [Usage Examples](usage.md)

---

## Security Notes

**Private Key Storage:**
- Location: `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem`
- ⚠️ **Never commit this file to Git**
- ⚠️ **Never share the private key**
- ✅ Stored outside project directory
- ✅ User-only access (Windows ACL)

**App Scope:**
- Installed on: `edri2or-commits` account only
- Repository access: `project-38` only
- Cannot access other repositories or organizations

---

## Why GitHub App (vs Personal Access Token)?

**Benefits:**
1. **Granular permissions** — Only what's needed
2. **Repository-scoped** — Can't access other repos
3. **Auditable** — All actions show as "project-38-scribe[bot]"
4. **Revocable** — Can uninstall without affecting other tools
5. **No user impersonation** — Runs as bot, not personal account

---

## Next Steps

- [ ] Test App permissions (create test commit)
- [ ] Document usage patterns
- [ ] Create automation workflows using the App
- [ ] Set up rotation schedule for private key (if needed)

---

*Last Updated: 2025-12-18*
