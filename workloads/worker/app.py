# POC-03: Worker
# Queue → Worker → LLM → Issue #24 → Telegram

import os
import logging
import json
import time
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, abort, jsonify
from google.cloud import storage, secretmanager
import requests
import jwt

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
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID')
GITHUB_APP_PRIVATE_KEY_SECRET = os.environ.get('GITHUB_APP_PRIVATE_KEY_SECRET')
CONTROL_ROOM_ISSUE = 24
TELEGRAM_BOT_TOKEN_SECRET = os.environ.get('TELEGRAM_BOT_TOKEN_SECRET', 'telegram-bot-token')

# Validation
if not GITHUB_APP_ID:
    raise ValueError("GITHUB_APP_ID must be configured")
if not GITHUB_APP_PRIVATE_KEY_SECRET:
    raise ValueError("GITHUB_APP_PRIVATE_KEY_SECRET must be configured")

def get_secret(secret_name):
    """Retrieve secret from Secret Manager."""
    try:
        name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise

def get_github_app_private_key():
    """Retrieve GitHub App private key from environment variable.
    
    Note: Cloud Run injects the secret content directly into the env var
    via secretKeyRef, so we read it directly rather than calling Secret Manager.
    """
    private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY_SECRET')
    if not private_key:
        raise ValueError("GITHUB_APP_PRIVATE_KEY_SECRET not configured")
    return private_key

def generate_app_jwt():
    """Generate GitHub App JWT for authentication."""
    private_key = get_github_app_private_key()
    
    payload = {
        'iat': int(time.time()) - 60,
        'exp': int(time.time()) + 600,
        'iss': GITHUB_APP_ID
    }
    
    return jwt.encode(payload, private_key, algorithm='RS256')

def get_installation_access_token(installation_id):
    """Get installation access token for GitHub App."""
    app_jwt = generate_app_jwt()
    
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {app_jwt}',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    
    response = requests.post(url, headers=headers, timeout=5)
    response.raise_for_status()
    return response.json()['token']

def post_comment(installation_token, repo_full_name, issue_number, comment_body):
    """Post a comment to a GitHub issue."""
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {installation_token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments'
    payload = {'body': comment_body}
    
    # Rate limit protection: add delay
    time.sleep(0.5)
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    return response.json()

def call_llm(prompt, model='claude-sonnet-4-20250514'):
    """
    Call LLM API (Anthropic Claude).
    
    For POC-03, simplified - just echoes the prompt.
    Full implementation will call actual API with secret.
    """
    # TODO: Implement actual LLM call
    # For now, echo with marker
    return f"🤖 LLM Response (model: {model}):\n\n> {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n\n_[POC-03: LLM integration placeholder]_"

def send_telegram_message(chat_id, text):
    """
    Send message to Telegram chat.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
    
    Returns:
        dict: Telegram API response
    """
    try:
        bot_token = get_secret(TELEGRAM_BOT_TOKEN_SECRET)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Telegram message sent to chat_id={chat_id}")
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e.__class__.__name__}")
        raise

def load_payload_from_gcs(bucket, blob_name):
    """Load payload from GCS claim-check."""
    try:
        bucket_obj = storage_client.bucket(bucket)
        blob = bucket_obj.blob(blob_name)
        data_str = blob.download_as_text()
        return json.loads(data_str)
    except Exception as e:
        logger.error(f"Failed to load payload from GCS: {e}")
        raise

def process_github_event(payload, correlation_id):
    """
    Process GitHub issue_comment event.
    
    Flow:
    1. Extract metadata
    2. Check guards (bot, echo, control room)
    3. Post to Issue #24
    4. Call LLM if needed
    5. Post LLM response
    
    Returns:
        dict: Processing result
    """
    installation_id = payload.get('installation', {}).get('id')
    repo_full_name = payload.get('repository', {}).get('full_name')
    repo_owner = payload.get('repository', {}).get('owner', {}).get('login')
    issue_number = payload.get('issue', {}).get('number')
    comment_user = payload.get('comment', {}).get('user', {}).get('login')
    comment_user_type = payload.get('comment', {}).get('user', {}).get('type')
    comment_body = payload.get('comment', {}).get('body', '')
    
    logger.info(f"Processing GitHub event: repo={repo_full_name} issue=#{issue_number} user={comment_user} correlation_id={correlation_id}")
    
    # Validation
    if not all([installation_id, repo_full_name, repo_owner, issue_number, comment_user]):
        raise ValueError("Missing required fields in GitHub payload")
    
    # BOT GUARD
    if comment_user_type == 'Bot':
        logger.info(f"Ignored: bot user={comment_user}")
        return {'status': 'ignored', 'reason': 'bot_user'}
    
    # ECHO MARKER GUARD
    if 'P38_ECHO_ACK' in comment_body:
        logger.info("Ignored: echo marker detected")
        return {'status': 'ignored', 'reason': 'echo_marker'}
    
    # CONTROL ROOM SCOPE
    if issue_number != CONTROL_ROOM_ISSUE:
        logger.info(f"Ignored: issue=#{issue_number} (not Control Room)")
        return {'status': 'ignored', 'reason': 'not_control_room'}
    
    # Get installation token
    try:
        installation_token = get_installation_access_token(installation_id)
    except Exception as e:
        logger.error(f"Failed to get installation token: {e.__class__.__name__}")
        raise
    
    # For POC-03: Process as LLM query
    # Format: post received message + LLM response
    
    # Post acknowledgment
    ack_body = f"""✅ Worker received (correlation_id: `{correlation_id}`)
📥 From: @{comment_user}
🕐 Queued: `{datetime.utcnow().isoformat()}Z`

_Processing with LLM..._
<!-- P38_WORKER_ACK -->"""
    
    try:
        ack_result = post_comment(installation_token, repo_full_name, issue_number, ack_body)
        logger.info(f"ACK posted: comment_id={ack_result['id']}")
    except Exception as e:
        logger.error(f"Failed to post ACK: {e.__class__.__name__}")
        # Continue anyway
    
    # Call LLM
    llm_response = call_llm(comment_body)
    
    # Post LLM response
    response_body = f"""{llm_response}

---
📊 Metadata:
- Correlation ID: `{correlation_id}`
- Processed: `{datetime.utcnow().isoformat()}Z`
- Source: `github`
<!-- P38_ECHO_ACK -->"""
    
    try:
        response_result = post_comment(installation_token, repo_full_name, issue_number, response_body)
        logger.info(f"LLM response posted: comment_id={response_result['id']}")
        
        return {
            'status': 'processed',
            'ack_comment_id': ack_result.get('id'),
            'response_comment_id': response_result['id'],
            'correlation_id': correlation_id
        }
        
    except Exception as e:
        logger.error(f"Failed to post LLM response: {e.__class__.__name__}")
        raise

def process_telegram_event(payload, correlation_id):
    """
    Process Telegram update event.
    
    Flow:
    1. Extract message text and chat_id
    2. Post to Issue #24 as formatted comment
    3. Call LLM
    4. Post LLM response to Issue #24
    5. Send LLM response back to Telegram
    
    Returns:
        dict: Processing result
    """
    message = payload.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    user_name = message.get('from', {}).get('username') or message.get('from', {}).get('first_name', 'Unknown')
    text = message.get('text', '')
    
    logger.info(f"Processing Telegram event: chat_id={chat_id} user={user_name} correlation_id={correlation_id}")
    
    if not chat_id or not text:
        raise ValueError("Missing chat_id or text in Telegram payload")
    
    # For POC-03: Post to Issue #24 in fixed repo
    # Hardcoded for now - should be configurable
    repo_full_name = "edri2or-commits/project-38"
    installation_id = int(os.environ.get('GITHUB_INSTALLATION_ID', '0'))
    
    if installation_id == 0:
        raise ValueError("GITHUB_INSTALLATION_ID not configured")
    
    # Get installation token
    try:
        installation_token = get_installation_access_token(installation_id)
    except Exception as e:
        logger.error(f"Failed to get installation token: {e.__class__.__name__}")
        raise
    
    # Post to Issue #24
    issue_body = f"""📱 Telegram Message (correlation_id: `{correlation_id}`)

**From:** {user_name} (chat_id: `{chat_id}`)  
**Time:** `{datetime.utcnow().isoformat()}Z`

**Message:**
> {text}

---
_Processing with LLM..._
<!-- P38_TELEGRAM_INBOUND -->"""
    
    try:
        issue_result = post_comment(installation_token, repo_full_name, CONTROL_ROOM_ISSUE, issue_body)
        logger.info(f"Telegram message posted to Issue #24: comment_id={issue_result['id']}")
    except Exception as e:
        logger.error(f"Failed to post to Issue #24: {e.__class__.__name__}")
        raise
    
    # Call LLM
    llm_response = call_llm(text)
    
    # Post LLM response to Issue #24
    response_body = f"""🤖 LLM Response for Telegram user `{user_name}`

{llm_response}

---
📊 Metadata:
- Correlation ID: `{correlation_id}`
- Chat ID: `{chat_id}`
- Processed: `{datetime.utcnow().isoformat()}Z`
<!-- P38_ECHO_ACK -->"""
    
    try:
        response_result = post_comment(installation_token, repo_full_name, CONTROL_ROOM_ISSUE, response_body)
        logger.info(f"LLM response posted to Issue #24: comment_id={response_result['id']}")
    except Exception as e:
        logger.error(f"Failed to post LLM response to Issue #24: {e.__class__.__name__}")
        # Continue to Telegram anyway
    
    # Send response to Telegram
    try:
        telegram_result = send_telegram_message(chat_id, llm_response)
        logger.info(f"Response sent to Telegram chat_id={chat_id}")
        
        return {
            'status': 'processed',
            'issue_comment_id': issue_result['id'],
            'response_comment_id': response_result.get('id'),
            'telegram_message_id': telegram_result.get('result', {}).get('message_id'),
            'correlation_id': correlation_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send Telegram response: {e.__class__.__name__}")
        raise

@app.route('/', methods=['POST'])
def worker():
    """
    Worker endpoint - processes tasks from Cloud Tasks queue.
    
    Payload format:
    {
      "type": "inline" | "gcs",
      "source": "github" | "telegram",
      "correlation_id": "...",
      "data": {...} | null,
      "bucket": "..." (if type=gcs),
      "blob": "..." (if type=gcs)
    }
    """
    try:
        task_payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse task payload: {e}")
        abort(400)
    
    payload_type = task_payload.get('type')
    source = task_payload.get('source')
    correlation_id = task_payload.get('correlation_id')
    
    logger.info(f"Worker processing task: type={payload_type} source={source} correlation_id={correlation_id}")
    
    # Load actual payload
    if payload_type == 'gcs':
        # Claim-check: load from GCS
        bucket = task_payload.get('bucket')
        blob = task_payload.get('blob')
        
        if not bucket or not blob:
            logger.error("Missing bucket/blob in GCS claim-check")
            abort(400)
        
        payload = load_payload_from_gcs(bucket, blob)
    elif payload_type == 'inline':
        payload = task_payload.get('data')
    else:
        logger.error(f"Unknown payload type: {payload_type}")
        abort(400)
    
    # Process based on source
    try:
        if source == 'github':
            result = process_github_event(payload, correlation_id)
        elif source == 'telegram':
            result = process_telegram_event(payload, correlation_id)
        else:
            logger.error(f"Unknown source: {source}")
            abort(400)
        
        logger.info(f"Worker completed: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Worker processing failed: {e.__class__.__name__}: {str(e)}")
        # Return 500 to trigger Cloud Tasks retry
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'service': 'worker'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port)
