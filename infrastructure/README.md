# Dify on Railway - Infrastructure Deployment

Deploy Dify (Community Edition) to Railway via **GitHub Actions** with automated secret management from GCP Secret Manager.

---

## 🚀 Quick Deploy

### Deployment via GitHub Actions (RECOMMENDED)

**Zero-Touch Deployment with GCP Secret Manager Integration:**

1. **Prerequisites:**
   - ✅ `RAILWAY_TOKEN` configured in GitHub Secrets
   - ✅ `RAILWAY_PROJECT_ID` configured in GitHub Secrets
   - ✅ GCP Workload Identity Federation configured (from Phase 1)
   - ✅ `OPENAI_API_KEY` stored in GCP Secret Manager

2. **Deploy:**
   - Go to: [GitHub Actions - Deploy to Railway](https://github.com/edri2or-commits/project-38/actions/workflows/deploy-railway.yml)
   - Click **"Run workflow"**
   - Select environment (production/staging)
   - Click **"Run workflow"** button

**The workflow will automatically:**
- 🔐 Authenticate to GCP via Workload Identity Federation
- 🔍 Fetch `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` from Secret Manager
- 🔑 Generate secure passwords for PostgreSQL, Redis, SECRET_KEY
- 🚀 Deploy to Railway with all variables configured
- ✅ Report deployment status in GitHub Actions summary

**Time:** ~2-3 minutes, **ZERO manual configuration!** ✨

---

## 📋 Environment Variables

All environment variables are **automatically configured** by the GitHub Actions workflow:

| Variable | Source | Auto-Generated |
|----------|--------|----------------|
| `POSTGRES_USER` | Hardcoded (`dify`) | N/A |
| `POSTGRES_PASSWORD` | OpenSSL random | ✅ Yes |
| `POSTGRES_DB` | Hardcoded (`dify`) | N/A |
| `REDIS_PASSWORD` | OpenSSL random | ✅ Yes |
| `SECRET_KEY` | OpenSSL random | ✅ Yes |
| `OPENAI_API_KEY` | GCP Secret Manager | 🔍 Auto-discovered |
| `ANTHROPIC_API_KEY` | GCP Secret Manager | 🔍 Auto-discovered |

**No manual password generation required!**

---

## 🔐 One-Time Setup

### 1. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

```bash
# Required secrets
RAILWAY_TOKEN         # Get from: https://railway.app/account/tokens
RAILWAY_PROJECT_ID    # Get from Railway project settings
```

**How to add secrets:**
1. Go to: `Settings` → `Secrets and variables` → `Actions`
2. Click **"New repository secret"**
3. Add `RAILWAY_TOKEN` and `RAILWAY_PROJECT_ID`

### 2. GCP Secret Manager Setup (One-Time)

Store your LLM API keys in GCP Secret Manager:

```bash
# Store OpenAI key (required)
echo -n "sk-proj-..." | gcloud secrets create openai-api-key \
  --data-file=- \
  --project=project-38-ai

# Store Anthropic key (optional)
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --project=project-38-ai
```

**After this setup:** Every deployment runs with ZERO manual input! 🎉

---

## 🏗️ Architecture

This deployment includes **5 services**:

1. **PostgreSQL (postgres)** - Database with persistent volume
2. **Redis (redis)** - Cache and message queue
3. **Dify API (dify-api)** - Backend API server
4. **Dify Worker (dify-worker)** - Async task processor (Celery)
5. **Dify Web (dify-web)** - Frontend web interface (Next.js)

### Service Dependencies

```
postgres ──┬──> dify-api ──┬──> dify-web
redis ─────┘               └──> dify-worker
```

---

## 📦 Persistent Storage

### PostgreSQL Volume
- **Mount Path:** `/var/lib/postgresql/data`
- **Volume Name:** `postgres-data`
- **Purpose:** Stores all database data

### Dify Storage Volume
- **Mount Path:** `/app/storage`
- **Volume Name:** `dify-storage`
- **Purpose:** Stores uploaded files, embeddings, and cache
- **Shared by:** `dify-api` and `dify-worker`

---

## 🌐 Accessing Dify

After deployment completes (~5 minutes):

1. Railway will provide a public URL for the `dify-web` service
2. Open the URL in your browser
3. Create your admin account on first access
4. Start building AI applications!

**Default Service URLs:**
- Frontend: `https://<dify-web-railway-domain>.railway.app`
- API: `https://<dify-api-railway-domain>.railway.app`

---

## 🔧 Advanced Configuration

### Trigger Deployment on Push to Main

The workflow is configured to **automatically deploy** on pushes to `main` branch (excluding documentation changes):

```yaml
on:
  push:
    branches:
      - main
    paths-ignore:
      - 'docs/**'
      - '**.md'
```

**To enable:** Just push to `main` - deployment runs automatically! 🚀

### Deploy to Staging Environment

```bash
# Manual workflow dispatch with staging environment
gh workflow run deploy-railway.yml -f environment=staging
```

### View Deployment Status

Check deployment progress:
- **GitHub Actions:** https://github.com/edri2or-commits/project-38/actions/workflows/deploy-railway.yml
- **Railway Dashboard:** https://railway.app/project/<PROJECT_ID>

---

## 🔄 Updating Dify

To update Dify to the latest version:

**Option 1: Via GitHub Actions (Recommended)**
1. Go to GitHub Actions → Deploy to Railway
2. Click "Run workflow"
3. Deployment will pull latest images automatically

**Option 2: Via Railway Dashboard**
1. Go to Railway dashboard → Select service
2. Click **"Redeploy"** for:
   - `dify-api`
   - `dify-worker`
   - `dify-web`
3. Railway will pull the latest `langgenius/dify-*:latest` images

---

## 🐛 Troubleshooting

### Workflow Failures

**Issue:** "RAILWAY_TOKEN not set"  
**Solution:** Add `RAILWAY_TOKEN` to GitHub Secrets (Settings → Secrets and variables → Actions)

**Issue:** "GCP auth failed"  
**Solution:** Verify Workload Identity Federation is configured correctly (from Phase 1)

**Issue:** "Secret not found in GCP Secret Manager"  
**Solution:** Run the GCP setup commands above to create secrets

### Service Health Checks

All services include health checks:

- **postgres:** `pg_isready` command (every 10s)
- **redis:** `redis-cli ping` command (every 10s)
- **dify-api:** HTTP GET `/health` endpoint (every 30s)
- **dify-web:** HTTP GET `http://localhost:3000` (every 30s)

### Common Issues

**Issue:** "Database connection failed"  
**Solution:** Check GitHub Actions logs - passwords are auto-generated and set correctly

**Issue:** "Redis connection refused"  
**Solution:** Wait 2-3 minutes for all services to start, check Railway logs

**Issue:** "Frontend shows 502 Bad Gateway"  
**Solution:** Wait 2-3 minutes for API service to fully start, check API health

---

## 📚 Additional Resources

- **GitHub Actions Workflow:** [.github/workflows/deploy-railway.yml](../.github/workflows/deploy-railway.yml)
- **Dify Official Docs:** https://docs.dify.ai
- **Railway Docs:** https://docs.railway.app
- **GCP Secret Manager:** https://cloud.google.com/secret-manager
- **Support:** Open an issue in this repository

---

## 🔒 Security Features

### Automated Security Hardening

✅ **Zero secrets in Git:** All credentials fetched from GCP Secret Manager  
✅ **OIDC/WIF authentication:** No static GCP credentials in GitHub  
✅ **Cryptographically secure passwords:** Generated with `openssl rand`  
✅ **Secrets masking:** GitHub Actions masks all sensitive values in logs  
✅ **Least privilege:** `github-actions-deployer` SA has minimal required permissions  
✅ **Audit trail:** All deployments logged in GitHub Actions history  

### Best Practices

1. ✅ **Never commit** `.env` files or secrets to Git
2. ✅ **Use GitHub Secrets** for Railway credentials
3. ✅ **Store LLM keys** in GCP Secret Manager
4. ✅ **Rotate secrets** regularly (every 90 days)
5. ✅ **Review deployment logs** for security warnings

---

## 🚀 Workflow Comparison

### Before (Manual Scripts)
```powershell
# 1. Run setup wizard locally
.\scripts\deployment\setup_env.ps1

# 2. Provide API keys manually
OPENAI_API_KEY: <type sk-...>

# 3. Run deployment script
.\scripts\deployment\deploy_railway.ps1
```
**Time:** ~5-10 minutes, requires local `gcloud` CLI

### After (GitHub Actions)
```bash
# Click "Run workflow" in GitHub UI
```
**Time:** ~2-3 minutes, ZERO local dependencies! ✨

---

## 📄 License

This infrastructure configuration follows the same license as Project 38.

Dify is licensed under the [Dify Open Source License](https://github.com/langgenius/dify/blob/main/LICENSE).
