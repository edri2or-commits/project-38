# Dify on Railway - Infrastructure Deployment

Deploy Dify (Community Edition) to Railway with one click using this pre-configured infrastructure setup.

---

## 🚀 Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/edri2or-commits/project-38&envs=POSTGRES_USER,POSTGRES_PASSWORD,POSTGRES_DB,REDIS_PASSWORD,SECRET_KEY,OPENAI_API_KEY,ANTHROPIC_API_KEY)

Click the button above to deploy Dify to Railway automatically.

---

## 📋 Required Environment Variables

Before deployment, you **must** configure the following environment variables in Railway:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `POSTGRES_USER` | PostgreSQL database username | `dify` | ✅ Yes |
| `POSTGRES_PASSWORD` | PostgreSQL database password (strong password) | `[generate-secure-password]` | ✅ Yes |
| `POSTGRES_DB` | PostgreSQL database name | `dify` | ✅ Yes |
| `REDIS_PASSWORD` | Redis password for cache/queue | `[generate-secure-password]` | ✅ Yes |
| `SECRET_KEY` | Dify secret key for session encryption | `[generate-secret-64-chars]` | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT models | `sk-...` | ⚠️ Optional* |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | `sk-ant-...` | ⚠️ Optional* |

**\*Note:** At least ONE LLM provider API key is required for Dify to function. You can add more providers later.

---

## 🔐 Environment Configuration

### Automated Setup (RECOMMENDED)

**Use the Setup Wizard for zero-touch configuration:**

```powershell
# Navigate to project root
cd C:\Users\edri2\project_38

# Run interactive setup wizard
.\scripts\deployment\setup_env.ps1
```

**The wizard will:**
- ✅ Auto-generate all secure passwords
- ✅ Prompt for LLM API key(s)
- ✅ Create `.env.production` file
- ✅ Optionally deploy to Railway

**See:** [Setup Wizard Guide](../scripts/deployment/README_setup_env.md)

### Manual Generation (Alternative)

<details>
<summary>Click to expand manual password generation</summary>

#### Strong Passwords (POSTGRES_PASSWORD, REDIS_PASSWORD)
```bash
# Generate a 32-character random password
openssl rand -base64 32
```

#### Secret Key (SECRET_KEY)
```bash
# Generate a 64-character secret key
openssl rand -hex 32
```

</details>

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
## 🔧 Configuration Notes

### Environment Variable References

Railway automatically provides these variables for service discovery:

- `${{RAILWAY_PRIVATE_DOMAIN_POSTGRES}}` - Internal PostgreSQL hostname
- `${{RAILWAY_PRIVATE_DOMAIN_REDIS}}` - Internal Redis hostname
- `${{RAILWAY_PUBLIC_DOMAIN_DIFY_API}}` - Public API domain (for frontend)

### Networking

Services communicate over Railway's **private network** using:
- PostgreSQL: Port `5432` (internal only)
- Redis: Port `6379` (internal only)
- Dify API: Port `5001` (public + internal)
- Dify Web: Port `3000` (public)

---

## 🛠️ Manual Deployment (Alternative)

If you prefer manual deployment:

1. **Fork this repository**
2. **Create a new Railway project**
3. **Add services from the `infrastructure/railway.json` file**
4. **Configure environment variables** in Railway dashboard
5. **Deploy each service** in dependency order:
   - postgres → redis → dify-api → dify-worker, dify-web

---
## 🔄 Updating Dify

To update Dify to the latest version:

1. Go to Railway dashboard → Select service
2. Click **"Redeploy"** for:
   - `dify-api`
   - `dify-worker`
   - `dify-web`
3. Railway will pull the latest `langgenius/dify-*:latest` images

---

## 🐛 Troubleshooting

### Service Health Checks

All services include health checks:

- **postgres:** `pg_isready` command (every 10s)
- **redis:** `redis-cli ping` command (every 10s)
- **dify-api:** HTTP GET `/health` endpoint (every 30s)
- **dify-web:** HTTP GET `http://localhost:3000` (every 30s)

### Common Issues

**Issue:** "Database connection failed"  
**Solution:** Check `POSTGRES_*` environment variables match between services

**Issue:** "Redis connection refused"  
**Solution:** Verify `REDIS_PASSWORD` is set correctly in all services

**Issue:** "Frontend shows 502 Bad Gateway"  
**Solution:** Wait 2-3 minutes for API service to fully start, check API health

---
## 📚 Additional Resources

- **Dify Official Docs:** https://docs.dify.ai
- **Railway Docs:** https://docs.railway.app
- **Support:** Open an issue in this repository

---

## ⚠️ Security Best Practices

1. ✅ **Never commit** `.env` files or secrets to Git
2. ✅ **Use strong passwords** (minimum 32 characters)
3. ✅ **Rotate secrets** regularly (every 90 days)
4. ✅ **Enable Railway's private networking** for service communication
5. ✅ **Use environment variables** for ALL configuration

---

## 📄 License

This infrastructure configuration follows the same license as Project 38.

Dify is licensed under the [Dify Open Source License](https://github.com/langgenius/dify/blob/main/LICENSE).
