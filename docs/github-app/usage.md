# GitHub App Usage — project-38-scribe

**App:** project-38-scribe  
**Last Updated:** 2025-12-18

---

## Overview

This document provides practical examples of using `project-38-scribe` for automation tasks.

---

## Authentication Methods

### Method 1: Using PyGithub (Python)

**Installation:**
```bash
pip install PyGithub cryptography
```

**Code:**
```python
import jwt
import time
import requests
from github import Github, GithubIntegration

# Configuration
APP_ID = 12345  # Your App ID
PRIVATE_KEY_PATH = r"<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem"
INSTALLATION_ID = 67890  # Your Installation ID

# Step 1: Generate JWT
with open(PRIVATE_KEY_PATH, 'r') as key_file:
    private_key = key_file.read()

payload = {
    'iat': int(time.time()),
    'exp': int(time.time()) + (10 * 60),  # 10 minutes
    'iss': APP_ID
}

jwt_token = jwt.encode(payload, private_key, algorithm='RS256')

# Step 2: Get Installation Token
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Accept': 'application/vnd.github.v3+json'
}

response = requests.post(
    f'https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens',
    headers=headers
)

installation_token = response.json()['token']

# Step 3: Use GitHub API
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Now you can use the repo object
print(f"Repository: {repo.full_name}")
print(f"Default branch: {repo.default_branch}")
```

---

### Method 2: Using Octokit (Node.js)

**Installation:**
```bash
npm install @octokit/app @octokit/rest
```

**Code:**
```javascript
const { App } = require('@octokit/app');
const fs = require('fs');

// Configuration
const appId = 12345;  // Your App ID
const privateKey = fs.readFileSync('<LOCAL_PEM_PATH>/project-38-scribe.2025-12-18.private-key.pem', 'utf8');
const installationId = 67890;  // Your Installation ID

// Create App instance
const app = new App({
  appId: appId,
  privateKey: privateKey,
});

// Get installation client
const octokit = await app.getInstallationOctokit(installationId);

// Use the API
const { data: repo } = await octokit.rest.repos.get({
  owner: 'edri2or-commits',
  repo: 'project-38',
});

console.log(`Repository: ${repo.full_name}`);
console.log(`Default branch: ${repo.default_branch}`);
```

---

### Method 3: Direct REST API (curl)

**Step 1: Generate JWT**
```bash
# Use a JWT generation tool or library
# See: https://jwt.io/ or use Python/Node.js script
```

**Step 2: Get Installation Token**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/app/installations/INSTALLATION_ID/access_tokens
```

**Step 3: Use Installation Token**
```bash
curl -H "Authorization: token INSTALLATION_TOKEN" \
  https://api.github.com/repos/edri2or-commits/project-38
```

---

## Common Use Cases

### Use Case 1: Auto-Update Documentation

**Scenario:** Update `docs/context/phase_status.md` when a deployment completes.

**Python Example:**
```python
from github import Github

# Authenticate (see Method 1 above)
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Read current file
file_path = "docs/context/phase_status.md"
file = repo.get_contents(file_path)
current_content = file.decoded_content.decode()

# Modify content
updated_content = current_content.replace(
    "Status: 📋 PLANNED",
    "Status: ✅ DONE"
)

# Commit change
repo.update_file(
    path=file_path,
    message="Auto-update: Mark Slice 2A as DONE",
    content=updated_content,
    sha=file.sha,
    branch="main"
)

print("✅ Documentation updated")
```

---

### Use Case 2: Trigger Workflow Dispatch

**Scenario:** Trigger a deployment workflow programmatically.

**Python Example:**
```python
from github import Github

# Authenticate
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Trigger workflow
workflow = repo.get_workflow("deploy.yml")
workflow.create_dispatch(
    ref="main",
    inputs={
        "environment": "dev",
        "version": "v1.2.3"
    }
)

print("✅ Workflow triggered")
```

**Node.js Example:**
```javascript
await octokit.rest.actions.createWorkflowDispatch({
  owner: 'edri2or-commits',
  repo: 'project-38',
  workflow_id: 'deploy.yml',
  ref: 'main',
  inputs: {
    environment: 'dev',
    version: 'v1.2.3'
  }
});

console.log('✅ Workflow triggered');
```

---

### Use Case 3: Create Feature Branch

**Scenario:** Create a branch for automated documentation updates.

**Python Example:**
```python
from github import Github

# Authenticate
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Get latest commit SHA from main
main_branch = repo.get_branch("main")
base_sha = main_branch.commit.sha

# Create new branch
new_branch_name = "docs/auto-update-2025-12-18"
repo.create_git_ref(
    ref=f"refs/heads/{new_branch_name}",
    sha=base_sha
)

print(f"✅ Created branch: {new_branch_name}")
```

---

### Use Case 4: List and Cancel Old Workflow Runs

**Scenario:** Cancel stale workflow runs older than 1 hour.

**Python Example:**
```python
from github import Github
from datetime import datetime, timedelta

# Authenticate
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Get running workflows
runs = repo.get_workflow_runs(status="in_progress")

# Cancel old runs
one_hour_ago = datetime.utcnow() - timedelta(hours=1)
for run in runs:
    if run.created_at < one_hour_ago:
        run.cancel()
        print(f"✅ Cancelled run #{run.id} (started {run.created_at})")
```

---

### Use Case 5: Create Annotated Tag

**Scenario:** Tag a release with metadata.

**Python Example:**
```python
from github import Github

# Authenticate
github = Github(installation_token)
repo = github.get_repo("edri2or-commits/project-38")

# Get commit to tag
commit = repo.get_commit("main")

# Create annotated tag
tag = repo.create_git_tag(
    tag="v1.2.3",
    message="Release v1.2.3\n\nChanges:\n- Feature A\n- Bug fix B",
    object=commit.sha,
    type="commit"
)

# Create reference
repo.create_git_ref(f"refs/tags/{tag.tag}", tag.sha)

print(f"✅ Created tag: {tag.tag}")
```

---

## Rate Limits

**GitHub App Rate Limits:**
- **5,000 requests per hour** per installation
- Resets every hour
- Check current limit:

```python
rate_limit = github.get_rate_limit()
print(f"Remaining: {rate_limit.core.remaining}/{rate_limit.core.limit}")
print(f"Resets at: {rate_limit.core.reset}")
```

**Best Practices:**
- Cache responses when possible
- Use conditional requests (ETag)
- Batch operations where available
- Monitor remaining quota

---

## Error Handling

**Common Errors:**

### 401 Unauthorized
```
Cause: Invalid or expired installation token
Solution: Regenerate installation token (max 1 hour lifetime)
```

### 403 Forbidden
```
Cause: Permission denied or rate limit exceeded
Solution: Check permissions.md or wait for rate limit reset
```

### 404 Not Found
```
Cause: File/branch/repo doesn't exist or App lacks access
Solution: Verify resource exists and App is installed
```

**Example Error Handling:**
```python
from github import GithubException

try:
    repo.update_file(path, message, content, sha)
except GithubException as e:
    if e.status == 401:
        print("Token expired, regenerating...")
        # Regenerate installation token
    elif e.status == 403:
        print(f"Permission denied or rate limited: {e.data}")
    elif e.status == 404:
        print(f"Resource not found: {e.data}")
    else:
        print(f"Error {e.status}: {e.data}")
        raise
```

---

## Security Best Practices

1. **Never commit private key:**
   ```bash
   # Add to .gitignore
   *.pem
   .github-app-config.yaml
   ```

2. **Rotate private key periodically:**
   - Generate new key in GitHub settings
   - Update automation scripts
   - Revoke old key

3. **Use short-lived tokens:**
   - Installation tokens expire after 1 hour
   - Regenerate for each automation run
   - Never cache tokens long-term

4. **Audit App activity:**
   - Review commits by "project-38-scribe[bot]"
   - Check GitHub audit log weekly
   - Monitor for unexpected actions

5. **Limit token scope:**
   - Only generate installation tokens for project-38
   - Never share tokens between environments
   - Revoke tokens after use (optional)

---

## Testing Checklist

Before deploying automation:

- [ ] Test read operations (get file, list commits)
- [ ] Test write operations (create file, update file)
- [ ] Test workflow triggers (dispatch, re-run)
- [ ] Test branch creation/deletion
- [ ] Test error handling (invalid file, missing permissions)
- [ ] Verify commit attribution (shows as bot)
- [ ] Check rate limit monitoring
- [ ] Review audit log for expected actions

---

## Troubleshooting

### Problem: "Resource not accessible by integration"

**Cause:** App lacks required permission  
**Solution:** Check [permissions.md](permissions.md) and update App permissions if needed

### Problem: Installation token generation fails

**Cause:** Invalid JWT or expired JWT  
**Solution:** 
- Verify App ID is correct
- Check private key file path
- Ensure JWT expiration is within 10 minutes

### Problem: Commits not showing as bot

**Cause:** Using wrong authentication method  
**Solution:** Use installation token, not personal access token

---

## Helper Scripts

**Location:** `scripts/github-app/` (to be created)

**Planned scripts:**
- `generate_token.py` — Generate installation token
- `update_docs.py` — Auto-update documentation
- `trigger_workflow.py` — Trigger workflow dispatch
- `audit_activity.py` — Review App activity

---

## References

- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [Octokit.js Documentation](https://github.com/octokit/octokit.js)
- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub App Authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app)

---

*Last updated: 2025-12-18*
