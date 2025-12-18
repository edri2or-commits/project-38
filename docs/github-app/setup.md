# GitHub App Setup — project-38-scribe

**Date:** 2025-12-18  
**Executor:** Or (edri2or)  
**Status:** ✅ COMPLETE

---

## Setup History

### Step 1: Create GitHub App

**Location:** GitHub.com → Settings → Developer settings → GitHub Apps → New GitHub App

**Configuration:**

```yaml
App Name: project-38-scribe
Homepage URL: https://github.com/edri2or-commits/project-38

Webhook:
  Active: ☐ Disabled (not needed)
  URL: (empty)
  Secret: (empty)

Post-Installation:
  Setup URL: (empty)
  Redirect on update: ☐ Disabled

Install Location:
  ⦿ Only on this account (edri2or-commits)
```

**Rationale for No Webhook:**
- No webhook endpoint available yet
- Current infrastructure: N8N on localhost:5678 (SSH tunnel only)
- Temporary Cloudflare Tunnel exists but unstable URL
- Webhook can be added later if push notifications needed
- GitHub App works fine without webhooks (polling/manual triggers)

---

### Step 2: Configure Permissions

**Repository Permissions:**

| Permission | Access Level | Rationale |
|------------|--------------|-----------|
| Actions | Read and write | Enable workflow dispatch, re-run jobs |
| Contents | Read and write | Create/update files, commits, branches |
| Workflows | Read and write | Modify workflow files in `.github/workflows/` |
| Metadata | Read-only | Automatic (required for all Apps) |

**Organization Permissions:**
- None (not needed for single-repo access)

**Account Permissions:**
- None (not needed for current use case)

**Subscribe to Events:**
- None (webhook disabled)

---

### Step 3: Generate Private Key

**Action:** GitHub App settings → "Generate a private key"

**Result:**
- Downloaded: `project-38-scribe.2025-12-18.private-key.pem`
- Saved to: `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem`
- Format: RSA private key (PEM format)
- Used for: Authenticating as the GitHub App

**Security Measures:**
- ✅ Stored outside project directory (won't be committed)
- ✅ User-only permissions (Windows ACL)
- ✅ Backed up separately (not in Git)

---

### Step 4: Install App on Repository

**Action:** GitHub App settings → "Install App"

**Configuration:**
- Target account: edri2or-commits
- Repository access: ⦿ Only select repositories
- Selected: ✓ project-38

**Result:**
- App installed on: `edri2or-commits/project-38`
- Installation ID: (assigned by GitHub)
- Permissions active: Actions R/W, Contents R/W, Workflows R/W

**Verification:**
- Repository settings → Integrations → GitHub Apps
- Shows: project-38-scribe (installed)

---

## App Identifiers

**The following identifiers are needed for API access:**

| Identifier | Purpose | Sensitivity |
|------------|---------|-------------|
| App ID | Identifies the App globally | Low (public) |
| Client ID | OAuth client identifier | Low (public) |
| Installation ID | Identifies App installation on repo | Low (public) |
| Private Key | Authenticates as the App | 🔴 HIGH (secret) |

**Where to Find:**
- App ID: GitHub → Settings → Developer settings → GitHub Apps → project-38-scribe
- Client ID: Same location
- Installation ID: `GET /repos/edri2or-commits/project-38/installation`
- Private Key: `<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem`

---

## Authentication Flow

**How the App authenticates:**

```
1. Generate JWT using:
   - App ID
   - Private Key (.pem file)
   - Expiration time (max 10 min)

2. Exchange JWT for Installation Token:
   POST /app/installations/{installation_id}/access_tokens
   Authorization: Bearer {JWT}

3. Use Installation Token for API calls:
   Authorization: token {installation_token}
   (Token valid for 1 hour, renewable)
```

**Libraries:**
- Python: `PyGithub`, `jwt`
- Node.js: `@octokit/app`, `jsonwebtoken`
- CLI: `gh` doesn't support App auth directly (use API)

---

## Testing the Installation

**Verify App has access:**

```bash
# Using GitHub CLI (with App credentials configured)
gh api /repos/edri2or-commits/project-38/installation

# Expected response:
{
  "id": <installation_id>,
  "app_id": <app_id>,
  "repository_selection": "selected",
  "permissions": {
    "actions": "write",
    "contents": "write",
    "workflows": "write",
    "metadata": "read"
  }
}
```

---

## Configuration Files

**For automation using this App:**

Create a config file (NOT committed):
```yaml
# .github-app-config.yaml (add to .gitignore)
app_id: <your_app_id>
installation_id: <your_installation_id>
private_key_path: <LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem
```

---

## Rollback / Uninstall

**If needed to remove the App:**

1. **Uninstall from repository:**
   - GitHub → Settings → Integrations → GitHub Apps
   - project-38-scribe → Configure → Uninstall

2. **Revoke private key:**
   - GitHub → Settings → Developer settings → GitHub Apps
   - project-38-scribe → Private keys → Revoke

3. **Delete App (if completely removing):**
   - GitHub → Settings → Developer settings → GitHub Apps
   - project-38-scribe → Advanced → Delete GitHub App

**Caution:** Deleting the App is irreversible. Uninstalling is reversible.

---

## Next Steps

- [ ] Document usage patterns (see [usage.md](usage.md))
- [ ] Create example automation scripts
- [ ] Test permissions with actual workflow
- [ ] Set up monitoring for API rate limits

---

## References

- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Authenticating as a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app)
- [GitHub Apps vs OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps)

---

*Setup completed: 2025-12-18*
