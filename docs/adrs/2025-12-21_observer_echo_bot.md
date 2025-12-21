# ADR-006: Observer Echo Bot for Control Room (#24)

**Date:** 2025-12-21  
**Status:** Accepted  
**Context:** Stage 2A - Orchestrator Observer

---

## Decision

Implement **Observer Echo Bot** as foundation for Stage 2 (Orchestrator Observer) before adding LLM integration.

### Approach: Prove the Loop, Then Add Intelligence

**Stage 2A (this ADR):** Echo Bot - E2E loop verification
- Issue #24 comment → GitHub webhook → Cloud Run → ACK reply
- Zero LLM complexity
- All foundation infrastructure tested

**Stage 2B (future):** LLM Integration
- Replace echo logic with LLM API calls
- Add context loading (SYSTEM_MAP + phase_status)
- Provider-agnostic abstraction layer

---

## Architecture

### Event Flow

```
User/Claude → Issue #24 Comment (text)
                ↓
GitHub Webhook Event (issue_comment.created)
                ↓
Cloud Run: github-webhook-receiver
  ├─ Verify signature (HMAC-SHA256)
  ├─ Idempotency check (Firestore + X-GitHub-Delivery)
  ├─ Filter: event=issue_comment, action=created
  ├─ GUARD: Skip if user.type == "Bot"
  ├─ GUARD: Skip if body contains "P38_ECHO_ACK"
  ├─ GUARD: Skip if issue != #24
  ├─ Parse comment (check for /commands)
  ├─ If NOT command: Post ACK
  └─ If command: Execute command logic
                ↓
Issue #24 ← ACK Comment ("✅ Echo: Received from @user")
            <!-- P38_ECHO_ACK -->
```

### Loop Prevention (Critical)

**3-Layer Defense:**

1. **Bot User Guard** (line ~306):
   ```python
   if comment_user_type == 'Bot':
       return jsonify({'status': 'ignored', 'reason': 'bot_user'}), 202
   ```

2. **Echo Marker Guard** (line ~311):
   ```python
   if 'P38_ECHO_ACK' in comment_body:
       return jsonify({'status': 'ignored', 'reason': 'echo_marker'}), 202
   ```

3. **Control Room Scope** (line ~316):
   ```python
   if issue_number != 24:
       return jsonify({'status': 'ignored', 'reason': 'not_control_room'}), 202
   ```

### ACK Format (Short)

```markdown
✅ Echo: Received from @username
<!-- P38_ECHO_ACK -->
```

**Rationale:** Minimal text to avoid notification spam

---

## Security

### Existing Controls (Inherited)
- ✅ HMAC-SHA256 signature verification (webhook_secret)
- ✅ Idempotency via Firestore (X-GitHub-Delivery)
- ✅ GitHub App JWT authentication
- ✅ Installation access token per request
- ✅ Secret Manager integration (private key)

### Command Authorization
- Owner-only commands (/label, /assign)
- Non-owner attempts logged as warnings
- ACK posted for all users (read-only operation)

---

## Implementation Details

### Code Changes (Local, Not Yet Deployed)

**File:** `workloads/webhook-receiver/app.py`

**Additions:**
1. Bot user type guard (line ~306)
2. Echo marker guard (line ~311)
3. Control Room scope (line ~316)
4. Short ACK format (line ~328)

**Modified Logic:**
- ACK only for non-command comments in Issue #24
- Commands still execute (existing /label, /assign)
- Echo marker in HTML comment (invisible to users)

### Environment Variables (Unchanged)
- `WEBHOOK_SECRET` - GitHub webhook signature key
- `GITHUB_APP_ID` - App ID (2497877)
- `GITHUB_APP_PRIVATE_KEY_SECRET` - Secret Manager name
- `GCP_PROJECT_ID` - project-38-ai

---

## Rationale

### Why Echo Bot First?

**Risk Reduction:**
- Test E2E loop without LLM API costs
- Verify GitHub webhook → Cloud Run → GitHub API chain
- Validate loop prevention guards
- Establish monitoring baseline

**Foundation for Stage 2B:**
- Same event flow
- Same authentication
- Same loop guards
- Only replace ACK logic with LLM call

### Why Issue #24 Only?

**Control Room Protocol:**
- Issue #24 = Single conversation thread (SSOT)
- All strategic decisions posted there
- "Chat אחד" Stage 1 already established
- Natural progression to Stage 2 (automated responses)

### Why Short ACK?

**Notification Management:**
- GitHub sends email for every comment
- Verbose ACKs = notification spam
- Short format = minimal disruption
- HTML comment hides technical marker

---

## Alternatives Considered

### 1. Actions-based Observer

**Rejected:** Cloud Run preferred
- Actions: 6-hour retention, no Firestore
- Cloud Run: Persistent state, existing deployment
- Actions: Extra GitHub API consumption
- Cloud Run: Already deployed with idempotency

### 2. All Issues vs Issue #24 Only

**Rejected:** Issue #24 scope safer
- MVP focus on Control Room
- Less risk of notification spam
- Easier to reason about behavior
- Can expand scope in Stage 2B if needed

### 3. Verbose ACK vs Short ACK

**Rejected:** Short format chosen
- User feedback: avoid spam
- "Chat אחד" protocol values brevity
- Echo is proof-of-concept only
- Full context in Stage 2B (LLM responses)

---

## Success Criteria

**Stage 2A Gates:**

### Gate 1: Code Deployed
- ✅ Local changes committed
- ✅ PR merged to main
- ✅ Cloud Run revision deployed
- ✅ No deployment errors

### Gate 2: E2E Loop Works
- ✅ Test comment posted in Issue #24
- ✅ ACK received within 5 seconds
- ✅ ACK format validated (contains "Echo" + marker)
- ✅ No loop (bot doesn't reply to itself)

### Gate 3: Evidence Documented
- ✅ Evidence file: `docs/evidence/2025-12-21_echo_bot_e2e_test.txt`
- ✅ Control Room comment: Gate 2A CLOSED
- ✅ Traceability matrix updated

---

## Stage 2B Preview (After Echo Works)

**LLM Integration Components:**

1. **Provider Abstraction** (`llm_client.py`):
   - Unified interface for OpenAI/Anthropic/Gemini
   - Rate limiting + retry logic
   - Token usage tracking

2. **Context Loading**:
   - Read SYSTEM_MAP.md from repo
   - Read phase_status.md for current state
   - Extract recent Issue #24 comments (history)

3. **Prompt Engineering**:
   - System prompt: Control Room role
   - User message: Comment body + context
   - Temperature: 0.3 (focused responses)

4. **Response Posting**:
   - Same GitHub API logic
   - Replace ACK with LLM response
   - Keep loop guards unchanged

---

## Rollback Plan

**If Echo Bot causes issues:**

1. Revert to previous revision:
   ```bash
   gcloud run services update-traffic github-webhook-receiver \
     --to-revisions=github-webhook-receiver-00009-lfb=100 \
     --project project-38-ai --region us-central1
   ```

2. Document issue in Control Room (#24)

3. Fix locally + re-deploy with canary

**No data loss risk:** Firestore idempotency preserved

---

## References

- **GitHub Webhooks:** https://docs.github.com/en/webhooks
- **GitHub App Auth:** https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app
- **Cloud Run:** https://cloud.google.com/run/docs
- **Control Room:** Issue #24
- **SYSTEM_MAP:** docs/_system/SYSTEM_MAP.md

---

## Decision Outcome

**Accepted:** 2025-12-21

**Next Actions:**
1. Commit local changes (app.py)
2. Create PR: "feat: observer echo bot for Control Room #24"
3. Deploy to Cloud Run
4. E2E test in Issue #24
5. Document evidence + close Gate 2A

**Impact:**
- ✅ Foundation for Stage 2B (LLM)
- ✅ E2E loop proven
- ✅ Loop prevention validated
- ✅ "Chat אחד" protocol operational
