# ADR-001: Webhook Receiver Deploy Provenance

**Date:** 2025-12-20  
**Status:** Accepted  
**Context:** Scribe MVP deployment alignment with SSOT (main branch)

---

## Status (2025-12-20)

### Content Alignment: VERIFIED ✅

**Evidence:**
- **Scope:** `workloads/webhook-receiver/` directory
- **Files verified:** `app.py`, `requirements.txt`
- **Method:** Git tree/blob hash comparison
- **Result:** webhook-receiver workload content matches main for app.py + requirements.txt
  - `app.py` blob hash: `68d42bd58ca4ae9951aaec90761f2965a9ca881d` (identical in b92e374 and e51cb35)
  - `requirements.txt` blob hash: `1a2a23f8647183f60dcad581a8025d1665946621` (identical in b92e374 and e51cb35)
- **Conclusion:** Production code content = main branch content

**Verification Commands:**
```bash
git diff b92e374 e51cb35 -- workloads/webhook-receiver/  # Output: empty (no differences)
git ls-tree -r b92e374 -- workloads/webhook-receiver/   # Blob hashes
git ls-tree -r e51cb35 -- workloads/webhook-receiver/   # Blob hashes (identical)
```

### Provenance Gap: DOCUMENTED ℹ️

**Deploy Method Used:**
```bash
gcloud run deploy github-webhook-receiver \
  --source workloads/webhook-receiver \
  --region us-central1 \
  --project project-38-ai
```

**How `--source` Works:**
- Uploads local directory to Cloud Storage
- Triggers Cloud Build to build container image
- Pushes built image to Artifact Registry (`cloud-run-source-deploy` repository)
- Deploys image to Cloud Run

**Reference:** [Cloud Run: Deploying from source code](https://docs.cloud.google.com/run/docs/deploying-source-code)
> "When you deploy from source code using the gcloud CLI [...], your source code is uploaded to a Cloud Storage bucket, and Cloud Build builds your source code into a container image. The container image is then pushed to Artifact Registry and deployed to Cloud Run."

**Limitation:**
- **Commit SHA not guaranteed to be derivable from runtime artifacts alone** (depends on deploy method)
- Build metadata contains GCS source path, not Git commit reference
- Image stored in `us-central1-docker.pkg.dev/project-38-ai/cloud-run-source-deploy/github-webhook-receiver`
- No Git commit SHA in Cloud Build sourceProvenance for directory-based deploys

**Reference:** [Artifact Registry: Integrate with Cloud Run](https://docs.cloud.google.com/artifact-registry/docs/integrate-cloud-run)
> "When you deploy directly from source code, Cloud Run stores the image in Artifact Registry in the cloud-run-source-deploy repository."

**Impact:**
- ✅ **Functional:** Zero impact (code content verified as correct)
- ❌ **Auditability:** Cannot trace production image → Git commit via metadata alone
- ℹ️ **SSOT Verification:** Requires manual Git comparison (as performed in this session)

---

## Decision

**Accept current state for MVP:**
- Content alignment verified via Git tree/blob hashes
- Provenance gap documented as known limitation
- Manual verification process sufficient for MVP stage

**Rationale:**
1. Code correctness confirmed (production = main content)
2. MVP functional requirements met (Scribe ACK working)
3. Provenance tracking not critical for current phase
4. Future enhancement path identified (CD pipeline)

---

## Backlog: Future Enhancement

**Goal:** Eliminate provenance gap via Git-based Continuous Deployment

**Approach:**
1. **Cloud Build Trigger** linked to GitHub repository
   - Trigger on: push to `main` branch
   - Source: Git clone (commit SHA preserved in build context)

2. **Build Configuration** (`cloudbuild.yaml`)
   - Use substitution variables: `$COMMIT_SHA`, `$SHORT_SHA`, `$BRANCH_NAME`
   - Tag images: `gcr.io/project-38-ai/github-webhook-receiver:$SHORT_SHA`

3. **Deploy from Tagged Image**
   - Deploy specific image tag (not `--source`)
   - Full audit trail: Git commit → Build → Image → Deploy

**Benefits:**
- ✅ Commit SHA in build metadata
- ✅ Image tags traceable to Git commits
- ✅ Automated deploy on merge
- ✅ Rollback by commit SHA

**References:**
- [Cloud Run: Continuous deployment](https://docs.cloud.google.com/run/docs/continuous-deployment)
- [Cloud Build: Create and manage build triggers](https://docs.cloud.google.com/build/docs/automating-builds/create-manage-triggers)
- [Cloud Build: Substitute variable values](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values)

**Priority:** Medium (post-MVP enhancement)

**Effort Estimate:** ~2-3 hours (setup + testing)

---

## Consequences

**Accepted:**
- Manual Git comparison required for SSOT verification
- Provenance gap exists until CD pipeline implemented
- Content verification process documented

**Benefits:**
- Clear documentation of limitation
- Verified code alignment for current deployment
- Path forward identified for future improvement

**Risks:**
- Manual verification prone to human error
- No automated audit trail for deployments
- Mitigation: Document verification process, implement CD in next phase

---

## References

- [Cloud Run: Deploying from source code](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Artifact Registry: Integrate with Cloud Run](https://docs.cloud.google.com/artifact-registry/docs/integrate-cloud-run)
- [Cloud Run: Continuous deployment](https://docs.cloud.google.com/run/docs/continuous-deployment)
- [Cloud Build: Create and manage build triggers](https://docs.cloud.google.com/build/docs/automating-builds/create-manage-triggers)
- [Cloud Build: Substitute variable values](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values)
