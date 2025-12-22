# ADR-001: GitHub Actions Now, Cloud Run Later

**Status:** ACCEPTED  
**Date:** 2025-12-22  
**Deciders:** Project 38 Team  
**Control Room:** [Issue #24](https://github.com/edri2or-commits/project-38/issues/24)

---

## Context

Stage 2B demonstrated IssueOps via GitHub Actions with OIDC/WIF to GCP. The system works but has architectural limitations that may require migration to Cloud Run in the future.

### GitHub Actions Limitations (Evidence-Based)

#### A) Concurrency Control (Non-Deterministic)
**Source:** https://docs.github.com/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs

**GitHub's `concurrency` field behavior:**
- ❌ **NOT a true queue**
- ⚠️ Max: 1 running + 1 pending job
- ⚠️ New run can **cancel** pending run
- ⚠️ **No order guarantee**

**Implication:**
```yaml
concurrency:
  group: issue-24-bot
  cancel-in-progress: true
```
This provides **best-effort** lock only. For deterministic execution order:
- ✅ Required: Label-based state machine (`processing` label)
- ✅ Required: Comment marker deduplication
- ✅ Required: Explicit checks before execution

#### B) Permissions API (author_association Deprecated)
**Source:** https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/

**Deprecated (removed by Oct 7, 2025):**
- ❌ `github.event.comment.author_association` field

**Required replacement:**
```bash
# REST API call in workflow
gh api repos/{owner}/{repo}/collaborators/{username}/permission
```

**Response:**
```json
{
  "permission": "admin"|"write"|"read"|"none",
  "role_name": "actual_role_including_custom"
}
```

**Policy:**
- Allow: `admin`, `maintain`, `push` (or chosen subset)
- Block: `read`, `none`

**Source:** https://docs.github.com/rest/collaborators/collaborators#get-repository-permissions-for-a-user

### Why GitHub Actions (Phase 1)

**Advantages:**
- ✅ Zero infrastructure (no webhooks, no servers)
- ✅ Built-in GITHUB_TOKEN (scoped access)
- ✅ OIDC/WIF to GCP (zero static secrets)
- ✅ Native GitHub integration (comments, labels, issues)
- ✅ Simple deployment (merge to main)
- ✅ Clear audit trail (workflow runs)

**Disadvantages:**
- ⚠️ Concurrency: Non-deterministic (requires protocol-level lock)
- ⚠️ Latency: ~10-30s cold start
- ⚠️ Timeout: 6 hours max per job
- ⚠️ Cost: Minutes charged (free tier: 2000/month)
- ⚠️ Rate limits: API throttling on high volume

### Why Cloud Run (Phase 2 - Future)

**Advantages:**
- ✅ True request queue (FIFO guaranteed)
- ✅ Sub-second cold start (GCR gen2)
- ✅ Horizontal scaling (0→1000+ instances)
- ✅ Advanced retry logic (exponential backoff)
- ✅ Native idempotency (request ID headers)
- ✅ Webhooks (direct GitHub → Cloud Run)
- ✅ Multi-channel support (Slack, Discord, etc.)
- ✅ Fine-grained concurrency control

**Disadvantages:**
- ❌ Infrastructure required (webhook endpoint)
- ❌ Manual OIDC/WIF setup for GitHub App
- ❌ More complex deployment (Cloud Run + Secret Manager)
- ❌ Higher operational overhead (monitoring, logs, alerts)

---

## Decision

**Phase 1 (NOW): GitHub Actions**
- Use GitHub Actions for Stage 2C (Protocol Hardening) and POC-03
- Implement deterministic controls at protocol level:
  - Label-based state machine (`processing` lock)
  - Comment ID deduplication markers
  - Permissions API (REST endpoint, not author_association)
- Accept best-effort `concurrency` field as optimization only

**Phase 2 (WHEN): Cloud Run**
- Migrate to Cloud Run when ANY of these triggers occur:
  - Latency requirements < 5 seconds
  - Request volume > 1000/day
  - Multi-channel expansion needed (Slack, Discord)
  - Advanced idempotency/retry required
  - User requests migration

---

## Consequences

### Positive
- ✅ Faster MVP delivery (Actions = simpler)
- ✅ Lower initial complexity
- ✅ Evidence-based migration (measure before moving)
- ✅ Protocol design portable (works on both platforms)

### Negative
- ⚠️ Concurrency requires protocol-level lock (not platform guarantee)
- ⚠️ Permissions require API call (not event field)
- ⚠️ Future migration work (Actions → Cloud Run)

### Neutral
- Protocol hardening (Step 2-3) applies to BOTH platforms
- Evidence-First Protocol remains unchanged
- SSOT (Issue #24) remains unchanged

---

## Implementation Notes

### Step 2 (Idempotency)
```yaml
# Check for existing marker
- name: Check Duplicate
  run: |
    COMMENT_ID="${{ github.event.comment.id }}"
    MARKER="P38_IDEMPOTENCY_KEY: comment_${COMMENT_ID}"
    
    gh api repos/${{ github.repository }}/issues/24/comments \
      --jq ".[] | select(.body | contains(\"$MARKER\")) | .id"
    
    # Exit if marker found (duplicate)
```

### Step 3 (State Machine)
```yaml
# Acquire processing lock
- name: Acquire Lock
  run: |
    LABELS=$(gh api repos/${{ github.repository }}/issues/24 --jq '.labels[].name')
    
    if echo "$LABELS" | grep -q "processing"; then
      echo "Lock held by another run"
      exit 1
    fi
    
    gh api repos/${{ github.repository }}/issues/24/labels \
      -X POST -f labels[]="processing"
```

---

## References

- [GitHub Actions Concurrency](https://docs.github.com/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs)
- [author_association Deprecation](https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/)
- [Permissions API](https://docs.github.com/rest/collaborators/collaborators#get-repository-permissions-for-a-user)
- [Stage 2B Evidence](../evidence/2025-12-21_stage_2b_llm_e2e.txt)
- [Control Room Issue #24](https://github.com/edri2or-commits/project-38/issues/24)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-22 | Initial decision (ACCEPTED) |
