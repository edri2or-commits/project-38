# Slice 1 Evidence Pack — VM Baseline (DEV)

**Phase:** Slice 1 (Infrastructure - VM Baseline)  
**Environment:** DEV (project-38-ai)  
**Status:** Evidence template (to be populated during execution)  
**Created:** 2024-12-15

---

## Purpose

This document defines EXACTLY what evidence must be captured during Slice 1 execution to prove completion and enable traceability.

**Rule:** No "DONE" without Evidence Pack complete.

---

## Evidence Items Required

### 1. Static IP Allocation

**Command:**
```bash
gcloud compute addresses describe project-38-dev-vm-01-ip \
  --region=<REGION> \
  --project=project-38-ai
```

**Required Fields in Output:**
- `address: <IP_ADDRESS>` (e.g., 34.56.78.90)
- `status: RESERVED` (before VM) → `status: IN_USE` (after VM)
- `addressType: EXTERNAL`
- `name: project-38-dev-vm-01-ip`

**Evidence Format:**
```yaml
# Static IP Evidence
timestamp: YYYY-MM-DDTHH:MM:SSZ
command: gcloud compute addresses describe...
output: |
  address: 34.56.78.90
  addressType: EXTERNAL
  creationTimestamp: '2024-12-15T10:30:00.000-08:00'
  id: '1234567890123456789'
  kind: compute#address
  name: project-38-dev-vm-01-ip
  region: https://www.googleapis.com/compute/v1/projects/project-38-ai/regions/us-central1
  selfLink: https://www.googleapis.com/compute/v1/projects/project-38-ai/regions/us-central1/addresses/project-38-dev-vm-01-ip
  status: IN_USE
  users:
  - https://www.googleapis.com/compute/v1/projects/project-38-ai/zones/us-central1-a/instances/project-38-dev-vm-01
```

---

### 2. Firewall Rules

**Command:**
```bash
gcloud compute firewall-rules list \
  --filter="name~'project-38-dev-'" \
  --format="table(name,network,direction,priority,sourceRanges.list():label=SRC_RANGES,allowed[].map().firewall_rule().list():label=ALLOW,targetTags.list():label=TARGET_TAGS)" \
  --project=project-38-ai
```

**Required Output (3 rules):**
```
NAME                          NETWORK  DIRECTION  PRIORITY  SRC_RANGES   ALLOW      TARGET_TAGS
project-38-dev-allow-ssh      default  INGRESS    1000      0.0.0.0/0    tcp:22     project-38-dev
project-38-dev-allow-http     default  INGRESS    1000      0.0.0.0/0    tcp:80     project-38-dev
project-38-dev-allow-https    default  INGRESS    1000      0.0.0.0/0    tcp:443    project-38-dev
```

**Evidence Format:**
```yaml
# Firewall Rules Evidence
timestamp: YYYY-MM-DDTHH:MM:SSZ
command: gcloud compute firewall-rules list...
rules_created:
  - name: project-38-dev-allow-ssh
    network: default
    direction: INGRESS
    priority: 1000
    sourceRanges: [0.0.0.0/0]
    allowed: [tcp:22]
    targetTags: [project-38-dev]
  - name: project-38-dev-allow-http
    network: default
    direction: INGRESS
    priority: 1000
    sourceRanges: [0.0.0.0/0]
    allowed: [tcp:80]
    targetTags: [project-38-dev]
  - name: project-38-dev-allow-https
    network: default
    direction: INGRESS
    priority: 1000
    sourceRanges: [0.0.0.0/0]
    allowed: [tcp:443]
    targetTags: [project-38-dev]
```

---

### 3. VM Instance Details

**Command:**
```bash
gcloud compute instances describe project-38-dev-vm-01 \
  --zone=<ZONE> \
  --project=project-38-ai
```

**Required Fields in Output:**
- `name: project-38-dev-vm-01`
- `status: RUNNING`
- `machineType: e2-medium` (or user-specified type)
- `serviceAccounts[0].email: n8n-runtime@project-38-ai.iam.gserviceaccount.com`
- `tags.items: [project-38-dev]`
- `networkInterfaces[0].accessConfigs[0].natIP: <STATIC_IP>`

**Evidence Format:**
```yaml
# VM Instance Evidence
timestamp: YYYY-MM-DDTHH:MM:SSZ
command: gcloud compute instances describe...
vm_details:
  name: project-38-dev-vm-01
  status: RUNNING
  machineType: https://www.googleapis.com/compute/v1/projects/project-38-ai/zones/us-central1-a/machineTypes/e2-medium
  zone: us-central1-a
  serviceAccounts:
    - email: n8n-runtime@project-38-ai.iam.gserviceaccount.com
      scopes: [https://www.googleapis.com/auth/cloud-platform]
  tags:
    items: [project-38-dev]
  networkInterfaces:
    - name: nic0
      network: default
      networkIP: 10.128.0.2
      accessConfigs:
        - name: External NAT
          natIP: 34.56.78.90
          type: ONE_TO_ONE_NAT
  disks:
    - boot: true
      diskSizeGb: '20'
      source: https://www.googleapis.com/compute/v1/projects/project-38-ai/zones/us-central1-a/disks/project-38-dev-vm-01
```

---

### 4. Docker Installation Verification

**Commands (run on VM via SSH):**
```bash
docker --version
docker compose version
sudo systemctl status docker
docker ps
```

**Required Output:**

#### docker --version
```
Docker version 24.0.7, build afdd53b
```

#### docker compose version
```
Docker Compose version v2.23.0
```

#### systemctl status docker
```
● docker.service - Docker Application Container Engine
     Loaded: loaded (/lib/systemd/system/docker.service; enabled; vendor preset: enabled)
     Active: active (running) since [timestamp]
```

#### docker ps (initially empty)
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

**Evidence Format:**
```yaml
# Docker Installation Evidence
timestamp: YYYY-MM-DDTHH:MM:SSZ
location: VM project-38-dev-vm-01

docker_version:
  command: docker --version
  output: "Docker version 24.0.7, build afdd53b"

docker_compose_version:
  command: docker compose version
  output: "Docker Compose version v2.23.0"

docker_service_status:
  command: sudo systemctl status docker
  output: |
    ● docker.service - Docker Application Container Engine
         Loaded: loaded (/lib/systemd/system/docker.service; enabled)
         Active: active (running) since 2024-12-15 18:45:30 UTC; 2min ago
         
docker_ps_initial:
  command: docker ps
  output: "CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES"
  note: "Empty as expected (no containers deployed yet)"
```

---

### 5. Service Account Secret Access Validation (METADATA ONLY)

**Commands:**
```bash
# Test n8n-encryption-key
gcloud secrets versions list n8n-encryption-key \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com

# Test postgres-password
gcloud secrets versions list postgres-password \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com

# Test telegram-bot-token
gcloud secrets versions list telegram-bot-token \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com
```

**Required Output (for EACH secret):**
```
NAME  STATE    CREATED              DESTROYED
2     enabled  2024-12-15T10:00:00
1     enabled  2024-12-15T09:55:00
```

**Evidence Format:**
```yaml
# Secret Access Validation Evidence
timestamp: YYYY-MM-DDTHH:MM:SSZ
note: "METADATA ONLY - no secret values accessed"

secret_access_tests:
  - secret_name: n8n-encryption-key
    command: gcloud secrets versions list n8n-encryption-key --project=... --impersonate-service-account=...
    result: SUCCESS
    versions_found: 2
    versions_enabled: 2
    
  - secret_name: postgres-password
    command: gcloud secrets versions list postgres-password --project=... --impersonate-service-account=...
    result: SUCCESS
    versions_found: 2
    versions_enabled: 2
    
  - secret_name: telegram-bot-token
    command: gcloud secrets versions list telegram-bot-token --project=... --impersonate-service-account=...
    result: SUCCESS
    versions_found: 2
    versions_enabled: 2

validation_status: ✅ PASS
note: "n8n-runtime SA can access all 3 required secrets (metadata confirmed)"
```

**CRITICAL:** No `gcloud secrets versions access` commands — values never retrieved.

---

## Timestamped Execution Log Format

**File:** `slice-01_execution_log.md`  
**Location:** `C:\Users\edri2\project_38\docs\phase-2\`

### Required Structure

```markdown
# Slice 1 Execution Log — VM Baseline (DEV)

**Execution Date:** YYYY-MM-DD
**Start Time:** HH:MM:SS UTC
**End Time:** HH:MM:SS UTC
**Duration:** X minutes Y seconds
**Executor:** Claude + User
**Status:** ✅ SUCCESS / ❌ FAILED / 🔄 PARTIAL

---

## Pre-Execution Checklist

- [x] Preflight Safety Checklist reviewed
- [x] User approval obtained
- [x] Region/zone confirmed: <REGION>/<ZONE>
- [x] All gcloud commands include --project project-38-ai

---

## Step 1: Reserve Static External IP

**Timestamp:** HH:MM:SS UTC

### Command Executed
```bash
gcloud compute addresses create project-38-dev-vm-01-ip \
  --region=us-central1 \
  --project=project-38-ai
```

### Output (RAW)
```
Created [https://www.googleapis.com/compute/v1/projects/project-38-ai/regions/us-central1/addresses/project-38-dev-vm-01-ip].
```

### Verification Command
```bash
gcloud compute addresses describe project-38-dev-vm-01-ip \
  --region=us-central1 \
  --project=project-38-ai
```

### Verification Output
```yaml
address: 34.56.78.90
addressType: EXTERNAL
creationTimestamp: '2024-12-15T10:30:00.000-08:00'
name: project-38-dev-vm-01-ip
status: RESERVED
```

### Result
✅ SUCCESS: Static IP allocated (34.56.78.90)

---

## Step 2: Create Firewall Rules

[Repeat structure for each firewall rule: ssh, http, https]

---

## Step 3: Create VM Instance

[Full command, output, verification]

---

## Step 4: Install Docker + Docker Compose

[SSH connection, installation commands, verification]

---

## Step 5: Validate Secret Access

[Impersonation tests for 3 secrets]

---

## Final Verification Checklist

- [x] VM status: RUNNING
- [x] Static IP assigned: 34.56.78.90
- [x] Firewall rules: 3 active
- [x] SSH access: confirmed
- [x] Docker version: 24.0.7
- [x] Docker Compose version: v2.23.0
- [x] Service account: n8n-runtime@project-38-ai.iam.gserviceaccount.com
- [x] Secret access (metadata): 3/3 pass

---

## Stop Condition Check

**Exit Criteria:** VM running with Docker installed, secret access validated
**Met:** ✅ YES
**Evidence:** All verification checks passed (see above)

---

## Artifacts Created

| Resource Type | Name | ID/IP | Status |
|--------------|------|-------|--------|
| Static IP | project-38-dev-vm-01-ip | 34.56.78.90 | IN_USE |
| Firewall Rule | project-38-dev-allow-ssh | tcp:22 | ENABLED |
| Firewall Rule | project-38-dev-allow-http | tcp:80 | ENABLED |
| Firewall Rule | project-38-dev-allow-https | tcp:443 | ENABLED |
| VM Instance | project-38-dev-vm-01 | 1234567890 | RUNNING |

---

## Next Steps

- ✅ Slice 1 complete — update traceability_matrix.md
- 📋 Ready for Slice 2 (Workload Deployment) when user approves
```

---

## Evidence Completeness Checklist

Before marking Slice 1 as DONE, verify:

- [ ] Static IP evidence captured (describe output)
- [ ] Firewall rules evidence captured (3 rules listed)
- [ ] VM instance evidence captured (describe output with SA confirmation)
- [ ] Docker installation evidence captured (version + systemctl status)
- [ ] Secret access validation evidence captured (3 secrets, metadata only)
- [ ] Execution log created with timestamps
- [ ] All commands include `--project project-38-ai`
- [ ] No secret values exposed anywhere
- [ ] Traceability matrix updated with evidence links

**If ALL checked:** Evidence Pack is complete ✅

---

## Redaction Rules

When capturing evidence:

1. **Secret values:** Replace with `[REDACTED]`
2. **API keys:** Replace with `[REDACTED]`
3. **Passwords:** Replace with `[REDACTED]`
4. **Tokens:** Replace with `[REDACTED]`

**Keep visible:**
- Secret names (e.g., "openai-api-key")
- Version numbers (e.g., "1", "2")
- Enabled/disabled status
- IAM bindings (service account emails)
- Metadata (creation timestamps, IDs)
- Resource names and IDs
- IP addresses (external IPs are not secrets)

---

## Storage Location

**Evidence Pack (this file):** `C:\Users\edri2\project_38\docs\phase-2\slice-01_evidence_pack.md`  
**Execution Log (during execution):** `C:\Users\edri2\project_38\docs\phase-2\slice-01_execution_log.md`

Both files referenced in `traceability_matrix.md` as evidence for Slice 1 completion.
