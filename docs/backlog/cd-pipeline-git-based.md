# Backlog: Git-based Continuous Deployment Pipeline

**Created:** 2025-12-20  
**Priority:** Medium (post-MVP)  
**Effort:** ~2-3 hours  
**Related:** ADR-001 (Webhook Receiver Deploy Provenance)

---

## Goal

Eliminate provenance gap by deploying from Git commits instead of directory uploads.

---

## Current State

### Deploy Method
```bash
gcloud run deploy github-webhook-receiver \
  --source workloads/webhook-receiver \
  --region us-central1 \
  --project project-38-ai
```

### Limitations
- **Method:** Directory upload → Cloud Build → Artifact Registry
- **Issue:** No Git commit SHA in build metadata
- **Status:** Content-aligned (verified), provenance untracked
- **Impact:** Manual verification required for SSOT alignment

**Reference:** [Cloud Run: Deploying from source code](https://docs.cloud.google.com/run/docs/deploying-source-code)

---

## Proposed Solution

### Architecture

```
GitHub (main branch)
  ↓ push event
Cloud Build Trigger
  ↓ clone repo with commit SHA
Build Container Image
  ↓ tag with $SHORT_SHA
Artifact Registry
  ↓ <REGION>-docker.pkg.dev/<PROJECT>/<REPO>/<IMAGE>:$SHORT_SHA
Cloud Run Deploy
  ↓ metadata includes commit SHA
Production (with full audit trail)
```

### Implementation Steps

#### Step 1: Create Cloud Build Trigger

**Trigger Configuration:**
- **Name:** `webhook-receiver-cd-main`
- **Event:** Push to branch `main`
- **Repository:** `github.com/edri2or-commits/project-38`
- **Build config:** `workloads/webhook-receiver/cloudbuild.yaml`
- **Substitutions:**
  - `_SERVICE_NAME=github-webhook-receiver`
  - `_REGION=us-central1`
  - `_PROJECT_ID=project-38-ai`

**Reference:** [Cloud Build: Create and manage build triggers](https://docs.cloud.google.com/build/docs/automating-builds/create-manage-triggers)

#### Step 2: Create Build Configuration

**File:** `workloads/webhook-receiver/cloudbuild.yaml`

```yaml
steps:
  # Build container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME:latest'
      - '.'
    dir: 'workloads/webhook-receiver'

  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - '$_SERVICE_NAME'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME:$SHORT_SHA'
      - '--region=$_REGION'
      - '--platform=managed'
      - '--project=$PROJECT_ID'

substitutions:
  _SERVICE_NAME: github-webhook-receiver
  _REGION: us-central1

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$_SERVICE_NAME:latest'

options:
  logging: CLOUD_LOGGING_ONLY
```

**Reference:** [Cloud Build: Substitute variable values](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values)

> **Note:** `gcr.io/...` pushes work only if you use **Artifact Registry `gcr.io` repositories**. Container Registry itself no longer accepts image writes (since 2025-03-18). Otherwise, push to Artifact Registry using `<REGION>-docker.pkg.dev/<PROJECT>/<REPO>/<IMAGE>:<TAG>`.
>
> **References:**
> - [Transition from Container Registry](https://docs.cloud.google.com/artifact-registry/docs/transition/transition-from-gcr)
> - [Prepare for Container Registry shutdown](https://docs.cloud.google.com/artifact-registry/docs/transition/prepare-gcr-shutdown)
> - [Artifact Registry gcr.io repositories](https://docs.cloud.google.com/artifact-registry/docs/transition/gcr-repositories)

#### Step 3: Grant IAM Permissions

```bash
# Grant Cloud Build service account permission to deploy to Cloud Run
gcloud projects add-iam-policy-binding project-38-ai \
  --member="serviceAccount:$(gcloud projects describe project-38-ai --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant Cloud Build service account permission to act as Cloud Run service account
gcloud iam service-accounts add-iam-policy-binding github-webhook-receiver-sa@project-38-ai.iam.gserviceaccount.com \
  --member="serviceAccount:$(gcloud projects describe project-38-ai --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=project-38-ai
```

#### Step 4: Test Trigger

1. Create `cloudbuild.yaml` in PR
2. Merge to `main`
3. Verify trigger executes
4. Check Cloud Run revision metadata for commit SHA

---

## Benefits

### Audit Trail
- ✅ Git commit SHA in build metadata
- ✅ Image tags traceable to commits (e.g., `us-central1-docker.pkg.dev/.../app:abc1234`)
- ✅ Deployment history linked to Git history

### Automation
- ✅ Deploy on merge (no manual intervention)
- ✅ Consistent build process
- ✅ Rollback by commit SHA

### SSOT Verification
- ✅ Production image tag = Git commit SHA
- ✅ Automated verification possible
- ✅ No manual Git comparison needed

---

## Risks & Mitigations

### Risk 1: Build Failures Block Deployments
**Mitigation:**
- Test builds in PR before merge
- Implement build status checks
- Manual rollback option available

### Risk 2: IAM Permission Issues
**Mitigation:**
- Grant minimal required permissions
- Test in DEV environment first
- Document permission requirements

### Risk 3: Build Time Increases
**Mitigation:**
- Use layer caching in Docker builds
- Optimize Dockerfile
- Monitor build performance

---

## Success Criteria

- [ ] Cloud Build trigger created and linked to GitHub
- [ ] `cloudbuild.yaml` committed to repository
- [ ] IAM permissions granted and tested
- [ ] First automated deploy successful
- [ ] Image tag includes commit SHA
- [ ] Cloud Run revision metadata includes commit reference
- [ ] Rollback tested (deploy older commit SHA)

---

## References

- [Cloud Run: Continuous deployment](https://docs.cloud.google.com/run/docs/continuous-deployment)
- [Cloud Build: Create and manage build triggers](https://docs.cloud.google.com/build/docs/automating-builds/create-manage-triggers)
- [Cloud Build: Substitute variable values](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values)
- [Cloud Run: Deploying from source code](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Artifact Registry: Integrate with Cloud Run](https://docs.cloud.google.com/artifact-registry/docs/integrate-cloud-run)
- [Transition from Container Registry](https://docs.cloud.google.com/artifact-registry/docs/transition/transition-from-gcr)
- [Prepare for Container Registry shutdown](https://docs.cloud.google.com/artifact-registry/docs/transition/prepare-gcr-shutdown)
- [Artifact Registry gcr.io repositories](https://docs.cloud.google.com/artifact-registry/docs/transition/gcr-repositories)

---

## Next Steps

1. Review ADR-001 for context
2. Create `cloudbuild.yaml` in feature branch
3. Test build configuration locally
4. Submit PR for review
5. Merge and verify automated deploy
