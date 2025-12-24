# POC-03: Full Conversation Flow - Runbook

## Architecture Deployed

```
GitHub/Telegram → Airlock (Cloud Run) → Queue (Cloud Tasks) → Worker (Cloud Run) → Issue #24 ↔ LLM
                                      ↓
                                   GCS (claim-check bucket)
```

## Services Deployed

### 1. Cloud Run Services
- **Airlock**: `github-webhook-receiver`
  - URL: https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app
  - Revision: github-webhook-receiver-00020-h8k
  - Image: gcr.io/project-38-ai/airlock:latest
  
- **Worker**: `worker`
  - URL: https://worker-u7gbgdjoja-uc.a.run.app
  - Revision: worker-00001-mp2
  - Image: gcr.io/project-38-ai/worker:latest

### 2. Cloud Tasks Queue
- **Name**: issue-commands-queue
- **Location**: us-central1
- **State**: RUNNING
- **Rate Limits**:
  - Max Concurrent: 5
  - Max Dispatches/sec: 10
- **Retry Config**:
  - Max Attempts: 5
  - Min Backoff: 2s
  - Max Backoff: 300s

### 3. GCS Bucket
- **Name**: project-38-ai-payloads
- **Location**: us-central1
- **Lifecycle**: Delete after 7 days

## Testing POC-03

### GitHub → Issue #24 Flow

1. **Post comment to Issue #24** (any user, non-command):
   ```
   Test message for POC-03
   ```

2. **Expected Flow**:
   - GitHub sends webhook to Airlock
   - Airlock verifies signature + idempotency
   - Airlock enqueues task to Cloud Tasks
   - Airlock returns 202 immediately
   - Worker picks up task from queue
   - Worker posts ACK to Issue #24
   - Worker calls LLM (placeholder in POC-03)
   - Worker posts LLM response to Issue #24

3. **Verify**:
   - Check Issue #24 for ACK comment (✅ Worker received)
   - Check Issue #24 for LLM response (🤖 LLM Response)
   - Verify correlation_id in all comments

### Telegram → Issue #24 Flow (Future)

1. **Send message to Telegram bot**:
   ```
   Hello from Telegram
   ```

2. **Expected Flow**:
   - Telegram sends webhook to Airlock
   - Airlock verifies token + idempotency
   - Airlock enqueues task to Cloud Tasks
   - Worker picks up task
   - Worker posts to Issue #24 (📱 Telegram Message)
   - Worker calls LLM
   - Worker posts LLM response to Issue #24
   - Worker sends LLM response back to Telegram

3. **Setup Required**:
   - Configure Telegram webhook: `https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook/telegram`
   - Set TELEGRAM_WEBHOOK_SECRET in Secret Manager

## Monitoring

### Cloud Run Logs
```bash
# Airlock logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=github-webhook-receiver" \
  --limit=50 --format="table(timestamp,textPayload)" --project=project-38-ai

# Worker logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=worker" \
  --limit=50 --format="table(timestamp,textPayload)" --project=project-38-ai
```

### Cloud Tasks Queue Status
```bash
gcloud tasks queues describe issue-commands-queue \
  --location=us-central1 --project=project-38-ai
```

### List Tasks in Queue
```bash
gcloud tasks list --queue=issue-commands-queue \
  --location=us-central1 --project=project-38-ai
```

## Manual Testing Commands

### Test Airlock Health
```bash
curl https://github-webhook-receiver-u7gbgdjoja-uc.a.run.app/health
# Expected: {"status":"ok","service":"airlock"}
```

### Test Worker Health
```bash
curl https://worker-u7gbgdjoja-uc.a.run.app/health
# Expected: {"status":"ok","service":"worker"}
```

### Simulate GitHub Webhook (Requires Signature)
```bash
# Not recommended - use actual GitHub comment instead
```

## Rollback

### Rollback Airlock
```bash
gcloud run services update-traffic github-webhook-receiver \
  --to-revisions=github-webhook-receiver-00019-jnb=100 \
  --region=us-central1 --project=project-38-ai
```

### Rollback Worker
```bash
# If needed - currently only one revision exists
gcloud run revisions list --service=worker \
  --region=us-central1 --project=project-38-ai
```

## Known Limitations (POC-03)

1. **LLM Integration**: Placeholder only - returns echo instead of actual LLM call
2. **Telegram**: Webhook endpoint exists but not configured with Telegram
3. **Authentication**: Worker is public (--allow-unauthenticated)
   - Should use Cloud Tasks authentication in production
4. **Rate Limiting**: Basic limits (5 concurrent, 10/sec)
   - May need tuning based on load
5. **Error Handling**: Retries configured but no DLQ

## Next Steps (Production)

1. Implement actual LLM API calls in Worker
2. Configure Telegram webhook
3. Add Worker authentication (Cloud Tasks service account)
4. Add Dead Letter Queue for failed tasks
5. Add metrics and alerting
6. Test end-to-end with real Telegram messages
7. Document in Issue #24 with correlation IDs

## Files Created

- `airlock.py` (296 lines) - Airlock service
- `worker.py` (420 lines) - Worker service
- `requirements.txt` (9 packages)
- `Dockerfile.airlock` - Airlock container
- `Dockerfile.worker` - Worker container

## Evidence Links

- Cloud Build Airlock: https://console.cloud.google.com/cloud-build/builds/60d4bc62-08e2-4a95-9804-cbdd9fd87be1?project=673161610630
- Cloud Build Worker: https://console.cloud.google.com/cloud-build/builds/d6b6d0c1-bcf1-434c-89f3-bbac3a9d87b3?project=673161610630
- Cloud Run Services: https://console.cloud.google.com/run?project=project-38-ai
- Cloud Tasks Queue: https://console.cloud.google.com/cloudtasks?project=project-38-ai
