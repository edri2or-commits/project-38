# Railway Zero-Touch Deployment Script

**Location:** `scripts/deployment/deploy_railway.ps1`

Fully automated PowerShell script for deploying Dify to Railway with **zero manual UI interaction**.

---

## 🎯 What This Script Does

1. **Checks Railway CLI** - Auto-installs if missing (via scoop or npm)
2. **Initializes Project** - Sets up Railway project connection
3. **Injects Variables** - Reads `.env.production` and uploads all secrets
4. **Deploys Infrastructure** - Launches all 5 Dify services automatically

**Zero clicks. Zero UI. 100% automation.**

---

## 📋 Prerequisites

### Required Files

1. **`.env.production`** in `infrastructure/` directory
   - **RECOMMENDED:** Use Setup Wizard (see Quick Start below)
   - **ALTERNATIVE:** Manual creation from template (not recommended)
   - **NEVER commit this file to Git** (already in .gitignore)

### Optional Tools (Script will install if missing)

- **Railway CLI** - Script auto-installs via:
  - Scoop (preferred), OR
  - npm, OR
  - Manual install instructions if both fail

---

## 🚀 Quick Start (RECOMMENDED)

### Zero-Touch Setup (One Command)

```powershell
# Navigate to project root
cd C:\Users\edri2\project_38

# Run interactive setup wizard
.\scripts\deployment\setup_env.ps1
```

**The wizard will:**
1. ✅ Auto-generate secure passwords (32-64 chars)
2. ✅ Prompt for your LLM API key(s)
3. ✅ Create `.env.production` automatically
4. ✅ Optionally deploy to Railway immediately

**Time:** ~5 minutes total

**See:** [Setup Wizard Guide](README_setup_env.md)

---

## 🔧 Alternative: Manual Setup (NOT RECOMMENDED)

<details>
<summary>Click to expand manual setup instructions</summary>

### Step 1: Create Environment File

```powershell
# Copy template to production config
Copy-Item infrastructure\.env.template infrastructure\.env.production

# Edit the file and fill in all values
notepad infrastructure\.env.production
```

### Step 2: Generate Secure Secrets

```powershell
# POSTGRES_PASSWORD (32 chars)
openssl rand -base64 32

# REDIS_PASSWORD (32 chars)
openssl rand -base64 32

# SECRET_KEY (64 chars hex)
openssl rand -hex 32
```

### Step 3: Run Deployment

```powershell
# Navigate to project root
cd C:\Users\edri2\project_38

# Execute deployment script
.\scripts\deployment\deploy_railway.ps1
```

</details>

---

## 📝 Script Parameters

### Basic Usage
```powershell
.\scripts\deployment\deploy_railway.ps1
```

### Advanced Options

```powershell
# Custom env file location
.\scripts\deployment\deploy_railway.ps1 -EnvFile "path\to\.env.custom"

# Skip Railway CLI installation check (if you know it's installed)
.\scripts\deployment\deploy_railway.ps1 -SkipInstallCheck

# Dry run (test without deploying)
.\scripts\deployment\deploy_railway.ps1 -DryRun
```

---

## 🔐 Required Environment Variables

| Variable | Description | Generate With |
|----------|-------------|---------------|
| `POSTGRES_USER` | PostgreSQL username | `dify` (example) |
| `POSTGRES_PASSWORD` | PostgreSQL password | `openssl rand -base64 32` |
| `POSTGRES_DB` | Database name | `dify` (example) |
| `REDIS_PASSWORD` | Redis password | `openssl rand -base64 32` |
| `SECRET_KEY` | Dify encryption key | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key* | From OpenAI dashboard |
| `ANTHROPIC_API_KEY` | Anthropic API key* | From Anthropic console |

**\*At least ONE LLM provider API key is required**

---

## 🎬 Execution Flow

```
[1/5] Check Railway CLI Installation
      ├─ Found? Continue
      └─ Not found? Auto-install (scoop/npm)

[2/5] Railway Project Initialization
      ├─ Check for .railway/ directory
      ├─ Login to Railway (opens browser)
      └─ Initialize project link

[3/5] Environment File Validation
      ├─ Check .env.production exists
      ├─ Parse all variables
      └─ Validate required fields

[4/5] Inject Environment Variables
      ├─ Read each variable from file
      ├─ Execute: railway variables --set KEY=VALUE
      └─ Progress: 7/7 variables uploaded ✓

[5/5] Launch Railway Deployment
      ├─ Execute: railway up --detach
      ├─ Monitor deployment start
      └─ Display status commands
```

---

## 📊 Example Output

```
=============================================
  Railway Zero-Touch Deployment
  Project 38 - Dify Infrastructure
=============================================

[1/5] Checking Railway CLI Installation
✅ Railway CLI is installed: railway version 3.5.0

[2/5] Railway Project Initialization
✅ Railway project already initialized (.railway directory found)
ℹ️  Current project status:
    Project: project-38-dify
    Environment: production

[3/5] Environment File Validation
✅ Environment file found: infrastructure\.env.production
✅ All required environment variables present
ℹ️  Found 7 environment variables to inject

[4/5] Injecting Environment Variables to Railway
ℹ️  Processing 7 environment variables...

  Setting POSTGRES_USER = dify ✓
  Setting POSTGRES_PASSWORD = ***xyz1 ✓
  Setting POSTGRES_DB = dify ✓
  Setting REDIS_PASSWORD = ***abc2 ✓
  Setting SECRET_KEY = ***def3 ✓
  Setting OPENAI_API_KEY = ***456a ✓
  Setting ANTHROPIC_API_KEY = ***789b ✓

✅ Variable injection complete: 7/7 succeeded

[5/5] Launching Railway Deployment
ℹ️  Deploying Dify infrastructure to Railway...
⚠️  This may take 5-10 minutes for initial deployment

✅ Deployment initiated successfully!

ℹ️  Monitor deployment status:
  railway status

ℹ️  View logs:
  railway logs

ℹ️  Open Railway dashboard:
  railway open

=============================================
  DEPLOYMENT COMPLETE!
=============================================

✅ Dify infrastructure deployed to Railway
```

---

## 🛠️ Troubleshooting

### Error: "Environment file not found"

**Solution:**
```powershell
# Create from template
Copy-Item infrastructure\.env.template infrastructure\.env.production

# Fill in required values
notepad infrastructure\.env.production
```

### Error: "Missing required environment variables"

**Solution:** Check that ALL required variables have values in `.env.production`

### Error: "Railway CLI installation failed"

**Manual Installation:**

**Option 1 (Recommended):**
```powershell
scoop install railway
```

**Option 2:**
```powershell
npm install -g @railway/cli
```

**Option 3:**
Download from https://docs.railway.app/develop/cli

### Error: "Deployment command failed"

**Check logs:**
```powershell
railway logs
```

**Verify project:**
```powershell
railway status
```

---

## 🔄 Post-Deployment

### Monitor Deployment
```powershell
railway status
```

### View Service Logs
```powershell
# All services
railway logs

# Specific service
railway logs -s dify-api
```

### Get Service URLs
```powershell
railway domain
```

### Open Dashboard
```powershell
railway open
```

---

## 🔒 Security Best Practices

1. ✅ **Never commit `.env.production`** - Already in .gitignore
2. ✅ **Use strong passwords** - Minimum 32 characters
3. ✅ **Rotate secrets regularly** - Every 90 days recommended
4. ✅ **Store backups securely** - Use password manager
5. ✅ **Limit access** - Only authorized team members

---

## 📚 Related Documentation

- **Railway Configuration:** `infrastructure/railway.json`
- **Deployment Guide:** `infrastructure/README.md`
- **Environment Template:** `infrastructure/.env.template`

---

## 🎯 Constitution Compliance

This script adheres to **CLAUDE.md** operational rules:

1. ✅ **NO LOCALHOST** - Deploys to Railway cloud
2. ✅ **ZERO MANUAL STEPS** - Fully automated deployment
3. ✅ **NO SECRETS** - All secrets via environment variables
4. ✅ **CLEAN ROOT** - Script in `scripts/deployment/`

---

*Last Updated: 2025-12-24*  
*Part of Project 38 - Phase 2: Dify Infrastructure*
