# ADR: Observer Echo Bot (Stage 2A)

**Date:** 2025-12-21  
**Status:** APPROVED  
**Decision:** Build Echo Bot before LLM integration

---

## Context

**Objective:** Establish "Chat אחד" protocol with Issue #24 as single conversation thread.

**Challenge:** High risk in combining multiple unknowns:
- GitHub issue_comment webhook handling
- GitHub API authentication (App installation tokens)
- LLM API integration
- Context management
- Response formatting

**Risk:** If any component fails, debugging is complex with multiple variables.

---

## Decision

**Build in 2 stages:**

### Stage 2A: Observer Echo Bot (THIS ADR)
**Purpose:** Prove E2E loop WITHOUT LLM complexity

**Flow:**
```
User/Claude → Issue #24 Comment
       ↓
GitHub Webhook (issue_comment.created)
       ↓
Cloud Run: orchestrator-observer
  - Verify: Issue #24 only
  - Verify: Not a bot comment
  - Extract: user, comment ID, timestamp
  - Format ACK: "✅ Echo: Received from @{user}"
  - POST to GitHub API
       ↓
Issue #24 ← ACK Comment (short)
```

**What This Proves:**
- ✅ Webhook routing works
- ✅ GitHub App auth works
- ✅ Comment creation works
- ✅ Loop prevention works
- ✅ Idempotency works

### Stage 2B: LLM Integration (FUTURE)
**Purpose:** Add intelligence to proven loop

**Flow:**
```
[Same webhook reception]
       ↓
Cloud Run: orchestrator-observer
  - Load context (SYSTEM_MAP + phase_status)
  - Call LLM API (OpenAI/Anthropic/Gemini)
  - Format response
  - POST to GitHub API
       ↓
Issue #24 ← LLM Response
```

---

## Architecture

### Component Reuse
**Extend existing:** `github-webhook-receiver` Cloud Run service

**Why not separate service:**
- Shared webhook endpoint (same signature verification)
- Shared Firestore idempotency (X-GitHub-Delivery)
- Shared GitHub App credentials
- Single deployment unit (simpler ops)

### Event Handler
**File:** `workloads/webhook-receiver/app.py`

**Add route:**
```python
@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    
    if event == 'issue_comment':
        return handle_issue_comment(request.json)
    elif event == 'issues':
        return handle_issues(request.json)
    # ... existing handlers
```

### Scope Controls (MANDATORY)

**1. Loop Prevention:**
```python
# Check 1: Bot detection
if payload['comment']['user']['type'] == 'Bot':
    return 'Ignored: Bot comment', 200

# Check 2: Echo marker
if 'P38_ECHO_ACK' in payload['comment']['body']:
    return 'Ignored: Echo marker detected', 200
```

**2. Issue #24 Only:**
```python
if payload['issue']['number'] != 24:
    return 'Ignored: Not Control Room', 200
```

**3. Action Filter:**
```python
if payload['action'] != 'created':
    return 'Ignored: Not created action', 200
```

**4. Idempotency (Reuse Existing):**
```python
delivery_id = request.headers.get('X-GitHub-Delivery')
if is_duplicate(delivery_id):
    return 'Duplicate delivery', 200
mark_processed(delivery_id)
```

### ACK Format (SHORT)

**Template:**
```
✅ Echo: Received from @{user}
<!-- P38_ECHO_ACK -->
```

**Why short:**
- Minimize notification spam
- Focus on E2E proof (not content)
- HTML comment preserves marker invisibly

**Max length:** ~50 characters (excluding marker)
---

## Implementation

### Phase 1: Code Extension (20 min)
- Add `handle_issue_comment()` function
- Implement 4 scope controls
- GitHub API integration (JWT + installation token)
- Short ACK formatting

### Phase 2: Deployment (10 min)
- Deploy to Cloud Run (existing service)
- Verify webhook configuration unchanged
- Test idempotency store access

### Phase 3: E2E Test (5 min)
- Post test comment in Issue #24
- Verify ACK appears in <5 seconds
- Verify loop prevention (ACK doesn't trigger ACK)

### Phase 4: Evidence (5 min)
- Create evidence file with webhook payload + logs
- Update Control Room Issue #24
- Update traceability_matrix.md

---

## Gates

### Gate A: Code Deployed
**Verify:**
- Cloud Run revision includes `issue_comment` handler
- Logs show event type recognition
- No deployment errors

**Evidence:** Cloud Run revision SHA + deployment timestamp

### Gate B: E2E Loop Works
**Verify:**
- Test comment posted to Issue #24
- ACK received within 5 seconds
- ACK format matches template
- No duplicate ACKs (idempotency verified)

**Evidence:** Issue #24 comment links + Cloud Run logs

### Gate C: Loop Prevention Works
**Verify:**
- ACK comment does NOT trigger another ACK
- Bot comments ignored (if any)
- Marker detection works

**Evidence:** Cloud Run logs showing "Ignored: Bot comment" or "Ignored: Echo marker"

---

## Consequences

### Positive
- ✅ Low-risk first step (no LLM complexity)
- ✅ Proves GitHub integration works
- ✅ Foundation for Stage 2B (LLM)
- ✅ Fast to build and test (~40 min total)
- ✅ Easy to debug (single responsibility)

### Neutral
- Manual testing required (post comment in Issue #24)
- ACK content not useful (just proof of concept)

### Negative
- None identified (this is pure risk reduction)

---

## Stage 2B Preview

**After Echo Bot works:**

1. **ADR:** Provider-agnostic LLM strategy
2. **Abstraction:** `llm_client.py` (OpenAI/Anthropic/Gemini)
3. **Context:** Load SYSTEM_MAP.md + phase_status.md
4. **Prompt:** Format with context + user comment
5. **Response:** Replace ACK with LLM output
6. **Deploy:** Same Cloud Run service (extend handler)

**Estimated effort:** 60-90 min (after Echo Bot proven)

---

## References

- Control Room: https://github.com/edri2or-commits/project-38/issues/24
- SYSTEM_MAP: docs/_system/SYSTEM_MAP.md
- Existing webhook-receiver: workloads/webhook-receiver/app.py
- GitHub App docs: docs/github-app/

---

## Decision Log

**Approved:** 2025-12-21  
**Approver:** edri2or  
**Conditions:**
1. Loop prevention (Bot + marker)
2. Scope control (Issue #24 only)
3. Idempotency (X-GitHub-Delivery)
4. Short ACK (no spam)
