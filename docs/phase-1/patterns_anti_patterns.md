# Project 38 V2 — Patterns & Anti-Patterns Analysis

**Source**: AIOS V1 Verified Facts  
**Date**: 2025-12-15  
**Status**: Pre-Build Planning Only

---

## Patterns to KEEP (עקרונות)

| Pattern | Evidence | Why Keep |
|---------|----------|----------|
| **Container-based isolation** | [VERIFIED] 6 separate containers (n8n, postgres, redis, qdrant, litellm, caddy) | Clear boundaries, independent scaling/restart, debuggable |
| **Health monitoring per service** | [VERIFIED] 5/6 healthy, litellm flagged UNHEALTHY | Early detection of service degradation |
| **Reverse proxy (Caddy)** | [VERIFIED] ai-os-caddy container healthy | Single entry point, HTTPS termination, routing abstraction |
| **External observability** | [VERIFIED] Langfuse cloud (not self-hosted) | Reduces operational burden, proven to work |
| **Incident documentation** | [VERIFIED] 4 incident files exist | Knowledge retention, pattern recognition for fixes |
| **VM-based runtime** | [VERIFIED] GCP VM us-central1-a, stable IP | Simple ops model, ssh debugging, proven stability |

---

## Anti-Patterns to AVOID (מה לא לחזור עליו)

| Anti-Pattern | Evidence | Root Cause | Prevention Concept |
|--------------|----------|------------|-------------------|
| **Credential injection hell** | [VERIFIED] GitOps blocker #1: "manual credential import path; secrets can't be in Git" | No standardized secret management | **Gate 0**: Adopt GCP Secret Manager from day 1 with env-var injection pattern |
| **Workflow activation requires UI** | [VERIFIED] GitOps blocker #2: "CLI can't activate reliably" | n8n API limitations or missing automation | **Pre-build**: Document n8n activation API + health check script as slice |
| **Env var drift** | [VERIFIED] GitOps blocker #3: "multiple sources of truth -> silent failures" | Manual edits in multiple places (VM, container, .env files) | **Single source**: One `.env` file per environment, mounted read-only into containers |
| **Silent component failures** | [VERIFIED] litellm UNHEALTHY but system still runs | No circuit breakers or dependency checks | **Health gates**: Startup dependency checks (n8n waits for postgres/redis UP) |
| **Missing env vars = silent death** | [VERIFIED] Personal agent "non-functional due to missing env vars" | Optional env vars treated as hard failures | **Explicit defaults**: All env vars must have fallback or fail-fast validation |

---

## Golden Flows (3–5 Core Patterns)

### Flow 1: Telegram → n8n → Response [VERIFIED Functional]

```
Trigger: Telegram webhook (HTTPS via Caddy)

Steps:
  1. Caddy receives POST /webhook/telegram → routes to n8n:5678
  2. n8n workflow "telegram-bot" activates
  3. [ASSUMPTION] Calls AI backend (litellm or direct model API)
  4. Returns response via Telegram Bot API

State: Telegram bot WORKING (per incidents notes)

Failure Modes:
  - Caddy down → webhook unreachable (503)
  - n8n down → no workflow execution
  - litellm UNHEALTHY → AI calls timeout or fallback
  
Recovery:
  - Auto-restart policy on containers (systemd or docker-compose restart: always)
  - Health check endpoint per service
```

---

### Flow 2: Personal Agent Activation [VERIFIED Broken]

```
Trigger: [ASSUMPTION] Scheduled cron or manual trigger

Steps:
  1. n8n workflow "personal-agent" attempts execution
  2. Reads env vars (e.g., GOOGLE_OAUTH_TOKEN, API_KEYS)
  3. Calls external APIs (Google Calendar, etc.)
  4. Executes actions

State: NON-FUNCTIONAL (missing env vars)

Failure Modes:
  - Missing env vars → workflow crashes at startup
  - No validation → silent failure or timeout
  
Recovery Concept:
  - Pre-flight validation: Script checks all required env vars BEFORE activation
  - Fail-fast: If env missing, refuse to activate workflow + alert
```

---

### Flow 3: Secrets Distribution [GitOps Blocker #1]

```
Current State (Anti-Pattern):
  - Manual import of credentials into n8n UI
  - Secrets stored locally in n8n postgres DB
  - No version control or rotation tracking

Desired Flow (Concept):
  Trigger: Deploy new version or secret rotation
  
  Steps:
    1. Secrets stored in GCP Secret Manager (1 secret per credential)
    2. Deployment script fetches secrets and injects as env vars
    3. n8n reads credentials from ENV (not manual import)
    4. Rotation = update Secret Manager → restart containers

  Verification:
    - All workflows activate without manual UI clicks
    - "List credentials" API call shows all required creds present
```

**Phase 2 Scope**: CORE secrets only
- n8n admin credentials
- Postgres password
- Telegram bot token
- LLM API key (OpenAI/Anthropic)

**DEFERRED**: Integration pack secrets (Make, Zapier, Notion, Google OAuth, etc.)

---

### Flow 4: Rollback on Failed Deploy [ASSUMPTION - Not Verified]

```
Trigger: New deployment breaks health checks

Steps:
  1. Deploy script pulls latest image/config
  2. Health check fails (n8n /healthz returns 500)
  3. Auto-rollback: Restore previous docker-compose.yml + env
  4. Restart containers with last-known-good config

State: [ASSUMPTION] Not implemented in V1

Prevention Concept:
  - Keep last 3 deploy snapshots (.env + compose files)
  - Atomic symlink swap (current -> v123 or v122)
  - Health gate: New version must pass 3 consecutive checks before marking stable
```

---

### Flow 5: Observability Trace [Partially Verified]

```
Trigger: Any n8n workflow execution

Steps:
  1. n8n generates execution_id
  2. Calls litellm (if AI step) with trace_id
  3. litellm logs to Langfuse cloud
  4. [ASSUMPTION] Context API logs workflow context

State: Langfuse VERIFIED as cloud service

Failure Modes:
  - litellm UNHEALTHY → traces dropped
  - No retry buffer → data loss

Prevention Concept:
  - Local trace buffer (redis queue) if litellm unavailable
  - Async batch upload to Langfuse
```

---

## Top 10 Pain Points (Root Cause + Prevention)

| # | Pain Point | Root Cause | Prevention Concept | Priority |
|---|-----------|------------|-------------------|----------|
| 1 | Manual credential import | No env-var credential injection | GCP Secret Manager + n8n env-var credentials | P0 |
| 2 | Workflow activation unreliable via CLI | n8n CLI doesn't register webhooks | API activation + production webhook verification | P0 |
| 3 | Env var drift across deployments | Multiple .env files, manual edits | Single source of truth (.env template in Git, secrets in SM) | P0 |
| 4 | litellm unhealthy but silent | No dependency health checks | Pre-flight validation script before n8n starts | P1 |
| 5 | Missing env vars kill workflows | No validation at deploy time | Startup script validates all REQUIRED env vars | P1 |
| 6 | No rollback mechanism | Manual recovery only | Automated rollback script + health gates | P1 |
| 7 | SSH required for debugging | No external monitoring/alerts | GCP Monitoring + health check alerts | P2 |
| 8 | Trace data loss (litellm down) | No local buffer | Redis queue + async Langfuse upload | P2 |
| 9 | Docker image version chaos | No tagging strategy | Semantic versioning + immutable tags | P2 |
| 10 | Incident knowledge scattered | Tribal knowledge in chat/files | Structured incident log + postmortem template | P3 |

---

## Verification Status Legend

- **[VERIFIED]**: Confirmed from AIOS V1 runtime facts (containers, logs, incidents)
- **[ASSUMPTION]**: Inferred from descriptions but not runtime-verified
- **[DEFERRED]**: Out of scope for Phase 2 baseline

---

**Document Version**: 1.0  
**Next Review**: After Slice 1 completion
