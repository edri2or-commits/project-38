# GitHub App Permissions — project-38-scribe

**App:** project-38-scribe  
**Last Updated:** 2025-12-18

---

## Permission Matrix

### Repository Permissions

| Permission | Level | Read Operations | Write Operations |
|------------|-------|----------------|------------------|
| **Actions** | Read and write | • List workflow runs<br>• Get run details<br>• Download artifacts<br>• View logs | • Re-run workflows<br>• Cancel runs<br>• Approve workflow runs<br>• Create workflow dispatch events |
| **Contents** | Read and write | • Read files<br>• List commits<br>• Get file metadata<br>• Clone repository<br>• List branches/tags | • Create/update files<br>• Create commits<br>• Create/delete branches<br>• Create/delete tags<br>• Push code |
| **Workflows** | Read and write | • Read workflow files<br>• List workflows<br>• Get workflow syntax | • Create workflow files<br>• Update workflow files<br>• Delete workflow files |
| **Metadata** | Read-only | • Repository info<br>• Collaborators list<br>• Repository topics | (Read-only permission) |

---

## Permission Use Cases

### Actions: Read and write

**Read Capabilities:**
```
- Check workflow run status
- Retrieve build logs
- Download build artifacts
- Monitor CI/CD pipeline health
```

**Write Capabilities:**
```
- Trigger workflow_dispatch events
- Re-run failed workflows automatically
- Cancel long-running workflows
- Approve pending workflow runs
```

**Example Use Cases:**
- Auto-retry failed deployments
- Trigger deployment workflows programmatically
- Cancel workflows on PR close
- Collect workflow metrics for reporting

---

### Contents: Read and write

**Read Capabilities:**
```
- Fetch file contents
- List directory structure
- Read commit history
- Analyze code changes
- Clone repository
```

**Write Capabilities:**
```
- Update documentation files
- Commit code changes
- Create feature branches
- Tag releases
- Merge branches (via commits)
```

**Example Use Cases:**
- Auto-update documentation from templates
- Generate changelogs on release
- Create branches for automated fixes
- Tag versions automatically
- Update version files (package.json, etc.)

---

### Workflows: Read and write

**Read Capabilities:**
```
- Parse workflow YAML files
- Validate workflow syntax
- List all workflows in repo
- Analyze workflow dependencies
```

**Write Capabilities:**
```
- Create new workflow files
- Update existing workflows
- Delete obsolete workflows
- Modify workflow triggers
- Add/remove workflow steps
```

**Example Use Cases:**
- Generate workflows from templates
- Update workflow versions (actions/checkout@v3 → v4)
- Add security scanning to all workflows
- Standardize workflow structure
- Create environment-specific workflows

---

### Metadata: Read-only

**Read Capabilities:**
```
- Get repository metadata
- List collaborators
- Check repository settings
- View repository topics
```

**Why Read-only:**
- This permission is automatically granted to all GitHub Apps
- Required for basic repository operations
- Cannot be elevated to write

**Example Use Cases:**
- Verify repository exists
- Check repository visibility (public/private)
- List team members
- Validate repository configuration

---

## Permission Boundaries

### What the App CAN Do

✅ Modify files in `docs/`, `src/`, etc.  
✅ Create/update workflows in `.github/workflows/`  
✅ Create branches and tags  
✅ Commit code changes  
✅ Trigger workflow runs  
✅ Read all repository content  

### What the App CANNOT Do

❌ Modify repository settings (visibility, features)  
❌ Manage webhooks  
❌ Create/delete the repository  
❌ Manage deploy keys  
❌ Modify branch protection rules  
❌ Access other repositories (scoped to project-38 only)  
❌ Manage organization settings  
❌ Invite/remove collaborators  
❌ Modify GitHub Pages settings  

---

## Security Implications

### Least Privilege Analysis

**Current permissions are appropriate for:**
- Documentation automation
- Workflow management
- CI/CD orchestration
- Release automation

**Permissions NOT granted (good):**
- Administration: Would allow repo deletion
- Deployments: Not needed (workflows handle this)
- Issues/PRs: Not needed for current use case
- Secrets: Not needed (workflows access secrets directly)

**Risk Assessment:**

| Permission | Risk Level | Mitigation |
|------------|------------|------------|
| Contents: Write | 🟡 Medium | App can push code, but commits are auditable and attributed to "project-38-scribe[bot]" |
| Workflows: Write | 🟡 Medium | Can modify CI/CD, but changes require review in workflow files |
| Actions: Write | 🟢 Low | Can trigger workflows, but workflows define what runs |
| Metadata: Read | 🟢 Low | Read-only, no risk |

**Overall Risk:** 🟡 Medium (acceptable for automation)

---

## Permission Audit Trail

**All actions by the App are logged:**

1. **Commit Attribution:**
   - Author: `project-38-scribe[bot]`
   - Email: `<app_id>+project-38-scribe[bot]@users.noreply.github.com`
   - Visible in: Git history, GitHub UI

2. **API Audit Log:**
   - GitHub Security Log shows all App API calls
   - Accessible: Settings → Security → Audit log
   - Filterable by: `action:apps.*`

3. **Workflow Triggers:**
   - Workflow runs show "Triggered by: project-38-scribe"
   - Visible in: Actions tab → specific run

**Monitoring:**
- Review App activity weekly
- Check for unexpected commits/workflow runs
- Audit branch creation/deletion

---

## Comparison: GitHub App vs PAT

| Feature | GitHub App (project-38-scribe) | Personal Access Token |
|---------|-------------------------------|---------------------|
| Scope | Single repo (project-38) | All repos user has access to |
| Attribution | Shows as "bot" | Shows as user |
| Permissions | Granular (4 specific) | Broad (repo = 8+ permissions) |
| Expiration | Private key doesn't expire | Varies by token type & org policy |
| Revocation | Uninstall app | Delete token |
| Rate Limit | 5,000 req/hour per installation | 5,000 req/hour per user |
| Audit | Clearly identified in logs | Mixed with user actions |
| Token Lifetime | Installation access token expires after 1 hour | Varies by token type & org policy |

**Winner:** GitHub App (better security, attribution, and scoping)

---

## Future Permission Changes

**If we need to add permissions later:**

1. GitHub → Settings → Developer settings → GitHub Apps
2. project-38-scribe → Permissions & events
3. Update permission level
4. User will be prompted to accept new permissions
5. Documentation: Update this file

**Common additions might include:**
- Issues: Write (for issue automation)
- Pull requests: Write (for PR automation)
- Deployments: Read (for deployment status)

**Do NOT add unless specific need identified.**

---

## References

- [GitHub Apps Permissions](https://docs.github.com/en/rest/overview/permissions-required-for-github-apps)
- [Fine-grained permissions](https://docs.github.com/en/apps/creating-github-apps/setting-up-a-github-app/choosing-permissions-for-a-github-app)
- [Rate limits for GitHub Apps](https://docs.github.com/en/rest/overview/rate-limits-for-the-rest-api#primary-rate-limit-for-github-app-installations)

---

*Last reviewed: 2025-12-18*
