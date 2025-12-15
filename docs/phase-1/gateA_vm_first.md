# Gate A Memo: VM vs Cloud Run for n8n

**Decision Point**: Infrastructure choice for Project 38 V2 baseline deployment  
**Date**: 2025-12-15  
**Status**: Planning — No builds executed  
**Blocker Resolution**: Must complete before Slice 1

---

## Executive Summary

**DECISION**: Start with **VM (Compute Engine)** for n8n + supporting services  
**Migration Path**: Stateless components (litellm) → Cloud Run in Phase 2B  
**Rationale**: Proven stability, debuggability, and webhook reliability outweigh cost optimization at baseline stage

---

## Decision Matrix

| Factor | VM (Compute Engine) | Cloud Run | Winner |
|--------|---------------------|-----------|--------|
| **SSH debugging** | ✅ Full access to logs, docker inspect, restart | ❌ Limited (logs only via console) | **VM** |
| **Proven stability** | ✅ V1 runs successfully on VM (6/6 containers) | ⚠️ Not tested for n8n workloads | **VM** |
| **Startup time** | ✅ Always-on (0ms) | ❌ Cold starts (1-5s) break webhook SLA | **VM** |
| **Stateful workflows** | ✅ Postgres + redis on same local network | ⚠️ Requires Cloud SQL ($25/mo extra) + VPC config | **VM** |
| **Cost (baseline)** | ~$25/mo (e2-medium, 4GB RAM) | ~$15/mo IF <1M requests/month | **VM** (predictable) |
| **Credential injection** | ✅ Mount secrets as files via startup script | ✅ Env vars from Secret Manager | **TIE** |
| **Rollback speed** | ✅ Swap docker-compose.yml (5s downtime) | ⚠️ Redeploy container image (30-60s) | **VM** |
| **Webhook reliability** | ✅ Static IP + always-on listener | ⚠️ Cold start may drop first request | **VM** |
| **Operational burden** | ⚠️ Manual patching, updates | ✅ Fully managed, auto-scaling | **Cloud Run** |

**Score**: VM wins 6/9 factors for baseline deployment

---

## Recommendation

### Phase 2A (Baseline) — **VM-First Architecture**

**Component Layout**:
```
GCP VM (e2-medium, us-central1-a)
├── Docker Compose orchestration
├── Caddy (reverse proxy + HTTPS)
├── n8n (workflow engine)
├── Postgres (n8n database)
├── Redis (cache + queue)
└── litellm (LLM proxy)
```

**Justification**:
1. **Risk Mitigation**: V1 proved this stack works in production
2. **Debuggability**: SSH access critical during baseline stabilization
3. **Webhook SLA**: Telegram webhooks require <3s response time (cold starts fail)
4. **Cost Predictability**: Fixed $25/mo vs variable Cloud Run costs during testing

---

### Phase 2B (Optimization) — **Hybrid Migration**

**Move litellm to Cloud Run ONLY** (stateless component):
- Benefit: Auto-scaling for LLM request spikes
- Risk: Minimal (litellm already shows UNHEALTHY in V1, isolated failure domain)
- Validation: Measure P99 latency before/after migration

**Keep on VM**:
- n8n (stateful, webhook-critical)
- Postgres (data persistence)
- Redis (low-latency cache)
- Caddy (stable reverse proxy)

---

### Phase 3 (Future) — **Full Cloud Run** (Conditional)

**Prerequisites** (must solve first):
1. n8n stateful workflow persistence on Cloud SQL
2. Webhook cold start mitigation (min instances = 1, but adds cost)
3. 3+ months of stable operations on VM baseline

**Decision Gate**: Revisit only if:
- VM costs exceed $50/mo (need horizontal scaling)
- OR operational burden (patching, monitoring) becomes blocker
- OR external compliance requirement forces managed services

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| **VM downtime during GCP maintenance** | Medium | High (all services offline) | [ACCEPT] Enable auto-restart on reboot + 99.5% GCP SLA | Ops |
| **Manual patching burden** | High | Medium (security vulns) | Automate: apt-get upgrade in startup script | DevOps |
| **No auto-scaling** | Low | Low (single-user workload) | [ACCEPT] Manual VM resize if usage grows | Product |
| **Lock-in to VM paradigm** | Medium | Medium (harder to migrate later) | Design litellm as stateless → validate Cloud Run path early | Architecture |
| **Insufficient VM resources** | Low | Medium (OOM kills containers) | Monitoring alerts on >80% RAM/CPU + resize runbook | Ops |

**Risk Acceptance**: VM downtime and manual patching are accepted trade-offs for baseline stability.

---

## Acceptance Criteria

Before marking Gate A as **PASSED**, verify:

### ✅ Baseline Deployment Health
```bash
# All containers running
docker ps | grep -E "(caddy|n8n|postgres|redis|litellm)" | wc -l
# Expected: 5

# n8n health check
curl -f https://[DOMAIN]/healthz
# Expected: HTTP 200

# Postgres connectivity
docker exec ai-os-postgres pg_isready -U n8n
# Expected: accepting connections
```

### ✅ Credential Flow (Zero Manual Import)
```bash
# Secrets fetched from GCP Secret Manager
./fetch_secrets.sh
cat .env | grep -E "(N8N_ENCRYPTION_KEY|TELEGRAM_BOT_TOKEN|OPENAI_API_KEY)"
# Expected: All values non-empty

# n8n credentials exist
docker exec ai-os-n8n n8n credentials:list
# Expected: ≥1 credential (no manual UI import)
```

### ✅ Rollback Capability
```bash
# Break deployment
echo "POSTGRES_PASSWORD=INVALID" >> .env
docker-compose restart postgres

# Health check fails
curl https://[DOMAIN]/healthz
# Expected: HTTP 500 or timeout

# Rollback
./rollback.sh

# Health restored
curl -f https://[DOMAIN]/healthz
# Expected: HTTP 200 within 30s
```

### ✅ Incident Response Time
```
# Measure: Time from alert to SSH access
- Alert fires (health check DOWN)
- Engineer receives notification
- SSH into VM
- Read logs (docker logs ai-os-n8n --tail 100)

Target: <2 minutes total
```

---

## Cost Projection

### VM Baseline (Month 1-3)
```
GCP e2-medium VM (4GB RAM, 2 vCPU): $24.27/mo
Static IP:                           $  6.57/mo
Disk (20GB SSD):                     $  3.40/mo
Egress (est. 10GB):                  $  1.20/mo
-------------------------------------------
TOTAL:                               ~$35/mo
```

### Hybrid (Month 4+, litellm on Cloud Run)
```
VM (e2-small downgrade, 2GB RAM):    $12.14/mo
Cloud Run litellm (1M requests):     $15.00/mo
Static IP:                           $  6.57/mo
Cloud SQL (DEFERRED):                $  0.00
-------------------------------------------
TOTAL:                               ~$34/mo
```

**Savings**: Minimal at single-user scale; optimization is for operational simplicity, not cost.

---

## Migration Trigger Points

**When to move litellm to Cloud Run** (Phase 2B):
- ✅ VM baseline stable for 30+ days
- ✅ litellm shows HEALTHY status consistently
- ✅ Langfuse traces working end-to-end

**When to consider full Cloud Run** (Phase 3):
- ⚠️ VM costs exceed $50/mo (need horizontal scaling)
- ⚠️ Manual ops burden blocks feature development
- ⚠️ Multi-user workload requires auto-scaling

**When NOT to migrate**:
- ❌ Baseline still unstable (incident rate >1/week)
- ❌ Webhook cold starts measured >500ms
- ❌ Cloud SQL migration effort not justified by workload

---

## Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2025-12-15 | VM-first for baseline | Proven stability + debuggability | **APPROVED** |
| TBD | litellm → Cloud Run | After 30 days stable VM operations | Pending |
| TBD | Full Cloud Run evaluation | Contingent on Phase 2B success | Deferred |

---

## Approval & Next Steps

**Gate A Status**: ✅ **APPROVED** for VM-first architecture

**Next Actions** (Planning only, no execution):
1. Document Slice 1 (VM provisioning steps)
2. Define CORE secrets list (n8n, postgres, telegram, LLM)
3. Draft docker-compose.yml (no deploy)
4. Create rollback.sh script template
5. Write health check endpoints spec

**Blocker for Slice 1 execution**: Await explicit "proceed" confirmation

---

**Document Version**: 1.0  
**Approval Date**: 2025-12-15  
**Next Review**: After Slice 3 (HTTPS endpoint live)
