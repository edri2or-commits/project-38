# POC-02 Proposal: Telegram Webhook Integration

**Status:** 📋 PROPOSED  
**Prerequisites:** POC-01 PASS ✅  
**Estimated Effort:** 2-3 hours

---

## Objective

Verify end-to-end Telegram → n8n webhook flow with:
1. Telegram webhook registration (`setWebhook`)
2. Message receipt + deduplication (`update_id`)
3. Basic response back to Telegram

---

## Prerequisites

### Required
| Item | Status | Notes |
|------|--------|-------|
| n8n running + activated | ✅ | POC-01 complete |
| Telegram Bot Token | ✅ | In Secret Manager (`telegram-bot-token`) |
| HTTPS endpoint | ❌ | **NEEDED** — see options below |

### HTTPS Options

**Option A: Domain + Let's Encrypt (Recommended for PROD)**
```
Domain: *.project38.ai or similar
Setup: Caddy/nginx reverse proxy with auto-SSL
Time: 1-2 hours
```

**Option B: ngrok tunnel (Quick POC)**
```
Setup: ngrok http 5678
Time: 5 minutes
Limitation: URL changes on restart, not for production
```

**Option C: Cloudflare Tunnel (Free, stable)**
```
Setup: cloudflared tunnel
Time: 30 minutes
Benefit: Stable URL, no port exposure
```

**Recommendation:** Option C for POC, Option A for production.

---

## POC Steps

### Phase 1: Setup HTTPS (choose option above)

### Phase 2: Register Webhook

```bash
# Get current webhook status
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

# Set webhook (replace URL)
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://YOUR_DOMAIN/webhook/telegram-bot"}'

# Verify
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
# Expected: {"ok":true,"result":{"url":"https://...","pending_update_count":0}}
```

### Phase 3: Create n8n Workflow

```json
{
  "name": "Telegram Echo Bot",
  "nodes": [
    {
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "telegram-bot",
        "httpMethod": "POST",
        "responseMode": "lastNode"
      }
    },
    {
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Deduplication + Echo\nconst update = $input.first().json;\nconst update_id = update.update_id;\nconst message = update.message?.text || 'No text';\nconst chat_id = update.message?.chat?.id;\n\n// TODO: Check update_id against Redis/DB for dedup\n\nreturn [{ json: { chat_id, text: `Echo: ${message}`, update_id } }];"
      }
    },
    {
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "operation": "sendMessage",
        "chatId": "={{ $json.chat_id }}",
        "text": "={{ $json.text }}"
      }
    }
  ]
}
```

### Phase 4: Test

```bash
# Send message to bot via Telegram app
# Check n8n executions
# Verify echo response received
```

### Phase 5: Idempotency Test

```bash
# Simulate duplicate webhook (replay attack)
curl -X POST "https://YOUR_DOMAIN/webhook/telegram-bot" \
  -H "Content-Type: application/json" \
  -d '{"update_id": 12345, "message": {"text": "test", "chat": {"id": 123}}}'

# Send same update_id twice
# Verify second request is deduplicated (no double response)
```

---

## Success Criteria

| Test | Expected |
|------|----------|
| `getWebhookInfo` | Shows registered URL |
| Send message to bot | n8n receives webhook |
| Bot responds | Echo message received in Telegram |
| Duplicate `update_id` | Second message ignored (dedup) |

---

## Deliverables

1. `docs/phase-2/poc-02_telegram_webhook.md` — Execution log
2. `deployment/n8n/workflows/telegram_echo_bot.json` — Workflow JSON
3. `docs/evidence/poc-02/` — Screenshots + curl outputs
4. Deduplication strategy decision (Redis vs DB vs in-memory)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| HTTPS setup complexity | Use Cloudflare Tunnel for POC |
| Telegram retry storms | Implement update_id dedup from day 1 |
| Bot token exposure | Already in Secret Manager, not in code |
| Webhook URL leak | Use random path suffix |

---

## Next After POC-02

If PASS → Ready for:
- Production domain setup
- Full conversation flow design
- State management (Redis/Firestore)
