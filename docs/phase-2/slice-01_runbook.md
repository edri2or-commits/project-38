# Slice 1 Runbook — VM Baseline (DEV)

**Phase:** Slice 1 (Infrastructure - VM Baseline)  
**Environment:** DEV (project-38-ai)  
**Status:** PRE-BUILD (Runbook ready, awaiting execution approval)  
**Created:** 2024-12-15

---

## Goal

Deploy minimal VM-first baseline infrastructure in DEV:
- Single Compute Engine VM running with n8n-runtime service account
- External static IP for direct internet access
- Firewall rules for SSH, HTTP, HTTPS
- Docker + Docker Compose installed and verified
- Secret access validation (metadata only)

**Approach:** Start simple, scale later if needed (no Cloud SQL/NAT/custom VPC initially)

---

## Inputs

| Parameter | Value | Notes |
|-----------|-------|-------|
| **GCP Project ID** | `project-38-ai` | MUST be included in every gcloud command |
| **Region** | TBD (suggest: us-central1 or europe-west1) | User decision |
| **Zone** | TBD (e.g., us-central1-a) | Same region as above |
| **VM Name** | `project-38-dev-vm-01` | Naming convention |
| **Machine Type** | `e2-medium` (2 vCPU, 4GB RAM) | User can override |
| **Boot Disk** | Ubuntu 24.04 LTS | 20GB standard persistent disk |
| **Service Account** | `n8n-runtime@project-38-ai.iam.gserviceaccount.com` | MUST be assigned to VM |
| **Network** | `default` | Using default VPC initially |
| **Static IP Name** | `project-38-dev-vm-01-ip` | Reserved external IP |
| **Firewall Tag** | `project-38-dev` | For firewall rule targeting |

---

## Outputs (Expected Results)

1. ✅ VM running and accessible via SSH
2. ✅ Static external IP assigned and pingable
3. ✅ Firewall rules allow SSH (22), HTTP (80), HTTPS (443)
4. ✅ Docker installed and running (`docker --version`)
5. ✅ Docker Compose installed (`docker compose version`)
6. ✅ VM has n8n-runtime service account attached
7. ✅ Service account can access its 3 secrets (metadata check only)

---

## Preflight Safety Checklist

**CRITICAL — Verify BEFORE execution:**

- [ ] Every gcloud command includes `--project project-38-ai`
- [ ] VM will run with SA: `n8n-runtime@project-38-ai.iam.gserviceaccount.com`
- [ ] Secret validation is METADATA ONLY (no `gcloud secrets versions access` for values)
- [ ] Using default VPC (no custom VPC creation)
- [ ] Static IP is external (not internal)
- [ ] Firewall rules target ONLY tagged VMs (not 0.0.0.0/0 unless necessary)
- [ ] Boot disk is 20GB minimum (for Docker images)
- [ ] Region/zone confirmed by user

**If ANY item unchecked → STOP and clarify with user before proceeding.**

---

## Step-by-Step Command Plan

### Step 1: Reserve Static External IP
**Purpose:** Allocate a stable external IP for the VM

```bash
gcloud compute addresses create project-38-dev-vm-01-ip \
  --region=<REGION> \
  --project=project-38-ai
```

**Verification:**
```bash
gcloud compute addresses describe project-38-dev-vm-01-ip \
  --region=<REGION> \
  --project=project-38-ai
```

**Expected Output:**
- Status: RESERVED
- Address type: EXTERNAL
- IP address: (will be shown)

---

### Step 2: Create Firewall Rules
**Purpose:** Allow SSH, HTTP, HTTPS to tagged VMs

#### Rule 1: Allow SSH (port 22)
```bash
gcloud compute firewall-rules create project-38-dev-allow-ssh \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=project-38-dev \
  --project=project-38-ai
```

#### Rule 2: Allow HTTP (port 80)
```bash
gcloud compute firewall-rules create project-38-dev-allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=project-38-dev \
  --project=project-38-ai
```

#### Rule 3: Allow HTTPS (port 443)
```bash
gcloud compute firewall-rules create project-38-dev-allow-https \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=project-38-dev \
  --project=project-38-ai
```

**Verification:**
```bash
gcloud compute firewall-rules list \
  --filter="name~'project-38-dev-'" \
  --project=project-38-ai
```

**Expected Output:**
- 3 rules listed (ssh, http, https)
- All enabled
- Network: default
- Target tags: project-38-dev

---

### Step 3: Create Compute Engine VM
**Purpose:** Deploy VM with n8n-runtime service account

```bash
gcloud compute instances create project-38-dev-vm-01 \
  --zone=<ZONE> \
  --machine-type=e2-medium \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard \
  --network-interface=network=default,address=project-38-dev-vm-01-ip \
  --tags=project-38-dev \
  --service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --project=project-38-ai
```

**Verification:**
```bash
gcloud compute instances describe project-38-dev-vm-01 \
  --zone=<ZONE> \
  --project=project-38-ai
```

**Expected Output:**
- Status: RUNNING
- Service account: n8n-runtime@project-38-ai.iam.gserviceaccount.com
- External IP: (matches reserved IP)
- Tags: project-38-dev

---

### Step 4: Install Docker + Docker Compose
**Purpose:** Prepare VM for containerized workloads

#### SSH into VM
```bash
gcloud compute ssh project-38-dev-vm-01 \
  --zone=<ZONE> \
  --project=project-38-ai
```

#### Install Docker (on VM)
```bash
# Update package list
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Verify Docker installation
docker --version
docker compose version
```

#### Verification (on VM)
```bash
# Check Docker service status
sudo systemctl status docker

# Test Docker
sudo docker run hello-world

# Verify Docker Compose
docker compose version
```

**Expected Output:**
- Docker version: 24.x or newer
- Docker Compose version: 2.x or newer
- Docker service: active (running)
- hello-world container runs successfully

---

### Step 5: Validate Service Account Secret Access
**Purpose:** Confirm n8n-runtime can access its 3 secrets (metadata only)

#### Test from local machine (impersonation)
```bash
# Test access to n8n-encryption-key
gcloud secrets versions list n8n-encryption-key \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com

# Test access to postgres-password
gcloud secrets versions list postgres-password \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com

# Test access to telegram-bot-token
gcloud secrets versions list telegram-bot-token \
  --project=project-38-ai \
  --impersonate-service-account=n8n-runtime@project-38-ai.iam.gserviceaccount.com
```

**Expected Output (for each secret):**
- Version 1: ENABLED
- Version 2: ENABLED
- No access denied errors

**CRITICAL:** Do NOT run `gcloud secrets versions access` — we only verify metadata (list versions), NOT actual secret values.

---

## Verification Checklist

After all steps complete, verify:

| Check | Command | Expected Result |
|-------|---------|-----------------|
| VM running | `gcloud compute instances list --project=project-38-ai` | Status: RUNNING |
| Static IP assigned | `gcloud compute addresses list --project=project-38-ai` | Address in use by VM |
| Firewall rules active | `gcloud compute firewall-rules list --filter="name~'project-38-dev-'" --project=project-38-ai` | 3 rules enabled |
| SSH works | `gcloud compute ssh project-38-dev-vm-01 --zone=<ZONE> --project=project-38-ai` | Connection successful |
| Docker installed | SSH to VM, run `docker --version` | Version 24.x+ |
| Docker Compose installed | SSH to VM, run `docker compose version` | Version 2.x+ |
| Docker service running | SSH to VM, run `sudo systemctl status docker` | Active (running) |
| Service account attached | `gcloud compute instances describe project-38-dev-vm-01 --zone=<ZONE> --project=project-38-ai` | SA: n8n-runtime@... |
| Secret access (metadata) | Impersonation tests (Step 5) | All 3 secrets show 2 ENABLED versions |

**If ALL checks pass:** Slice 1 is COMPLETE ✅

---

## Stop Conditions (When to STOP and NOT Proceed)

**STOP immediately if:**

1. ❌ Any gcloud command missing `--project project-38-ai`
2. ❌ VM created without n8n-runtime service account
3. ❌ Static IP allocation fails (quota exceeded or region unavailable)
4. ❌ Firewall rules fail to create (name conflict or permission issue)
5. ❌ VM fails to start (boot disk error, quota exceeded, zone unavailable)
6. ❌ Docker installation fails (network issues, package conflicts)
7. ❌ Service account CANNOT access its 3 secrets (IAM issue)
8. ❌ SSH connection to VM fails after 3 attempts

**Recovery Action:** STOP execution, document failure, consult rollback plan (slice-01_rollback_plan.md)

---

## Notes

- **Duration Estimate:** 1-2 hours (includes Docker installation + verification)
- **Cost Estimate:** ~$20-30/month for e2-medium VM + static IP (DEV environment)
- **Next Steps:** After Slice 1 completion, proceed to Slice 2 (Workload Deployment)
- **Evidence:** All execution details logged in `slice-01_execution_log.md` (created during execution)
