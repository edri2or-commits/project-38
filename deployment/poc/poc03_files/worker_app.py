import os
import logging
import time
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import storage, secretmanager

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize clients
storage_client = storage.Client()
secret_client = secretmanager.SecretManagerServiceClient()

# Load configuration
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'project-38-ai')
CLAIM_CHECK_BUCKET = os.environ.get('CLAIM_CHECK_BUCKET', 'project-38-ai-payloads')
CONTROL_ROOM_ISSUE = int(os.environ.get('CONTROL_ROOM_ISSUE', '24'))
CONTROL_ROOM_REPO = os.environ.get('CONTROL_ROOM_REPO', 'edri2or-commits/project-38')

# GitHub App credentials (from Secret Manager)
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID')
GITHUB_APP_PRIVATE_KEY_SECRET = os.environ.get('GITHUB_APP_PRIVATE_KEY_SECRET')

def get_secret(secret_name):
    """Retrieve secret from Secret Manager."""
    try:
        name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise

def load_payload_from_gcs(claim_check_uri):
    """Load payload from GCS using claim check URI."""
    # Parse gs://bucket/path
    if not claim_check_uri.startswith('gs://'):
        raise ValueError(f"Invalid claim check URI: {claim_check_uri}")

    parts = claim_check_uri[5:].split('/', 1)
    bucket_name = parts[0]
    blob_name = parts[1]

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    payload_json = blob.download_as_string()
    return json.loads(payload_json)

def generate_github_app_jwt():
    """Generate GitHub App JWT for authentication."""
    import jwt

    private_key = get_secret(GITHUB_APP_PRIVATE_KEY_SECRET)

    payload = {
        'iat': int(time.time()) - 60,
        'exp': int(time.time()) + 600,
        'iss': GITHUB_APP_ID
    }

    return jwt.encode(payload, private_key, algorithm='RS256')

def get_installation_token(installation_id):
    """Get installation access token for GitHub App."""
    app_jwt = generate_github_app_jwt()

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {app_jwt}',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'

    response = requests.post(url, headers=headers, timeout=5)
    response.raise_for_status()
    return response.json()['token']

def post_github_comment(installation_id, repo_full_name, issue_number, comment_body):
    """Post a comment to GitHub issue."""
    token = get_installation_token(installation_id)

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    url = f'https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments'
    payload = {'body': comment_body}

    # Add retry with exponential backoff for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)

            # Check rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining and int(remaining) < 10:
                logger.warning(f"GitHub API rate limit low: {remaining} remaining")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and 'rate limit' in e.response.text.lower():
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise

def call_llm(prompt, model='claude'):
    """Call LLM API (Claude or OpenAI)."""
    if model == 'claude':
        api_key = get_secret('anthropic-api-key')
        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        payload = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()['content'][0]['text']

    elif model == 'openai':
        api_key = get_secret('openai-api-key')
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'gpt-4',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 1024
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    else:
        raise ValueError(f"Unknown model: {model}")

def send_telegram_message(chat_id, text):
    """Send message to Telegram user."""
    bot_token = get_secret('telegram-bot-token')
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    return response.json()

@app.route('/process', methods=['POST'])
def process_task():
    """Process task from Cloud Tasks queue."""
    start_time = time.time()

    # Get correlation ID from header
    correlation_id = request.headers.get('X-Correlation-ID', 'unknown')

    logger.info(f"Worker received task: correlation_id={correlation_id}")

    try:
        # Parse task payload
        task_data = request.get_json()

        # Check if this is a claim check
        if 'claim_check_uri' in task_data:
            logger.info(f"Loading payload from claim check: {task_data['claim_check_uri']}")
            event_data = load_payload_from_gcs(task_data['claim_check_uri'])
        else:
            event_data = task_data

        # Extract event details
        source = event_data.get('source')
        metadata = event_data.get('metadata', {})
        payload = event_data.get('payload', {})

        logger.info(f"Processing event: source={source} correlation_id={correlation_id}")

        # STEP 1: Post incoming message to Control Room (Issue #24)
        if source == 'github':
            # GitHub comment -> already in Issue #24, just acknowledge
            installation_id = metadata.get('installation_id')
            comment_user = metadata.get('comment_user')
            comment_body = payload.get('comment_body', '')

            # Format: Log that we received it
            intake_comment = f"""🔄 **Worker Processing** (correlation_id: `{correlation_id}`)
**Source:** GitHub Issue Comment
**User:** @{comment_user}
**Status:** Processing with LLM...

<!-- POC03_WORKER_INTAKE -->"""

            intake_result = post_github_comment(
                installation_id,
                CONTROL_ROOM_REPO,
                CONTROL_ROOM_ISSUE,
                intake_comment
            )

            logger.info(f"Posted intake comment: {intake_result['id']}")

        elif source == 'telegram':
            # Telegram message -> post to Issue #24
            installation_id = metadata.get('installation_id')  # Need to configure this
            if not installation_id:
                # For POC, use hardcoded installation ID (get from existing payload)
                installation_id = 66225857  # From GitHub App

            username = metadata.get('username', 'unknown')
            message_text = payload.get('message_text', '')
            chat_id = metadata.get('chat_id')

            intake_comment = f"""📱 **Telegram Message** (correlation_id: `{correlation_id}`)
**From:** @{username} (chat_id: {chat_id})
**Message:**
```
{message_text}
```

**Status:** Processing...

<!-- POC03_TG_INTAKE -->"""

            intake_result = post_github_comment(
                installation_id,
                CONTROL_ROOM_REPO,
                CONTROL_ROOM_ISSUE,
                intake_comment
            )

            logger.info(f"Posted Telegram intake to Issue #24: {intake_result['id']}")

        # STEP 2: Call LLM for response
        if source == 'github':
            prompt = f"User comment: {comment_body}\n\nProvide a helpful, concise response."
        else:  # telegram
            prompt = f"User message: {message_text}\n\nProvide a helpful, concise response."

        logger.info(f"Calling LLM (Claude) for correlation_id={correlation_id}")
        llm_response = call_llm(prompt, model='claude')

        # STEP 3: Post LLM response to Control Room
        response_comment = f"""✅ **LLM Response** (correlation_id: `{correlation_id}`)

{llm_response}

---
**Model:** Claude Sonnet 4
**Processing Time:** {int((time.time() - start_time) * 1000)}ms

<!-- POC03_LLM_RESPONSE -->"""

        response_result = post_github_comment(
            installation_id,
            CONTROL_ROOM_REPO,
            CONTROL_ROOM_ISSUE,
            response_comment
        )

        logger.info(f"Posted LLM response: {response_result['id']}")

        # STEP 4: If source was Telegram, send response back to user
        if source == 'telegram':
            try:
                telegram_text = f"🤖 *Response:*\n\n{llm_response}"
                tg_result = send_telegram_message(chat_id, telegram_text)
                logger.info(f"Sent Telegram response: message_id={tg_result['result']['message_id']}")
            except Exception as e:
                logger.error(f"Failed to send Telegram response: {e}")
                # Post error to Issue #24
                error_comment = f"⚠️ Failed to send Telegram response (correlation_id: `{correlation_id}`): {e.__class__.__name__}"
                post_github_comment(installation_id, CONTROL_ROOM_REPO, CONTROL_ROOM_ISSUE, error_comment)

        elapsed = int((time.time() - start_time) * 1000)
        logger.info(f"Worker completed task in {elapsed}ms (correlation_id={correlation_id})")

        return jsonify({
            'status': 'completed',
            'correlation_id': correlation_id,
            'elapsed_ms': elapsed,
            'intake_comment_id': intake_result['id'],
            'response_comment_id': response_result['id']
        }), 200

    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        logger.error(f"Worker failed: {e.__class__.__name__} - {str(e)} (correlation_id={correlation_id}, elapsed={elapsed}ms)")

        # Try to post error to Control Room (best-effort)
        try:
            error_comment = f"""❌ **Worker Error** (correlation_id: `{correlation_id}`)
**Error:** `{e.__class__.__name__}`
**Message:** {str(e)}
**Elapsed:** {elapsed}ms

<!-- POC03_WORKER_ERROR -->"""

            # Use installation_id if available
            if 'installation_id' in locals():
                post_github_comment(installation_id, CONTROL_ROOM_REPO, CONTROL_ROOM_ISSUE, error_comment)
        except:
            pass

        return jsonify({
            'status': 'error',
            'correlation_id': correlation_id,
            'error': e.__class__.__name__,
            'elapsed_ms': elapsed
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'service': 'worker'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
