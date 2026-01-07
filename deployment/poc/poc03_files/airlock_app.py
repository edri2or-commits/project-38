import os
import hmac
import hashlib
import logging
import time
import json
from datetime import datetime, timedelta
from flask import Flask, request, abort, jsonify
from google.cloud import firestore, tasks_v2, storage
from google.cloud.exceptions import Conflict

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize clients
db = firestore.Client()
tasks_client = tasks_v2.CloudTasksClient()
storage_client = storage.Client()

# Load configuration from environment
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'project-38-ai')
QUEUE_LOCATION = os.environ.get('QUEUE_LOCATION', 'us-central1')
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'issue-commands-queue')
WORKER_URL = os.environ.get('WORKER_URL')  # Worker Cloud Run URL
CLAIM_CHECK_BUCKET = os.environ.get('CLAIM_CHECK_BUCKET', 'project-38-ai-payloads')
CLAIM_CHECK_THRESHOLD = int(os.environ.get('CLAIM_CHECK_THRESHOLD', '102400'))  # 100KB

if not WEBHOOK_SECRET:
    logger.error("WEBHOOK_SECRET environment variable not set")
    raise ValueError("WEBHOOK_SECRET must be configured")

if not WORKER_URL:
    logger.error("WORKER_URL environment variable not set")
    raise ValueError("WORKER_URL must be configured")

def verify_github_signature(payload_body, signature_header):
    """Verify GitHub webhook signature using HMAC-SHA256."""
    if not signature_header:
        return False

    try:
        hash_algorithm, github_signature = signature_header.split('=', 1)
    except ValueError:
        return False

    if hash_algorithm != 'sha256':
        return False

    mac = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()

    return hmac.compare_digest(expected_signature, github_signature)

def verify_telegram_token(token_header):
    """Verify Telegram webhook token."""
    return token_header == TELEGRAM_BOT_TOKEN

def check_idempotency(delivery_id, source='github'):
    """Check and record delivery ID for idempotency."""
    doc_ref = db.collection('webhook_deliveries').document(f"{source}_{delivery_id}")

    try:
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'seen',
            'source': source,
            'expireAt': datetime.utcnow() + timedelta(days=1)
        })
        return True  # First time seeing this delivery
    except Conflict:
        return False  # Duplicate delivery

def store_payload_in_gcs(payload, correlation_id):
    """Store large payload in GCS and return claim check URI."""
    bucket = storage_client.bucket(CLAIM_CHECK_BUCKET)
    blob_name = f"payloads/{correlation_id}.json"
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        json.dumps(payload),
        content_type='application/json'
    )

    claim_check_uri = f"gs://{CLAIM_CHECK_BUCKET}/{blob_name}"
    logger.info(f"Payload stored in GCS: {claim_check_uri} (size: {len(json.dumps(payload))} bytes)")

    return claim_check_uri

def enqueue_task(event_data, correlation_id):
    """Enqueue task to Cloud Tasks queue."""
    parent = tasks_client.queue_path(GCP_PROJECT_ID, QUEUE_LOCATION, QUEUE_NAME)

    # Determine if we need claim-check pattern
    payload_size = len(json.dumps(event_data))

    if payload_size > CLAIM_CHECK_THRESHOLD:
        # Store in GCS, send claim check
        claim_check_uri = store_payload_in_gcs(event_data, correlation_id)
        task_payload = {
            'correlation_id': correlation_id,
            'claim_check_uri': claim_check_uri,
            'metadata': event_data.get('metadata', {})
        }
    else:
        # Send payload directly
        task_payload = event_data

    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': WORKER_URL,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps(task_payload).encode()
        }
    }

    response = tasks_client.create_task(request={'parent': parent, 'task': task})
    logger.info(f"Task enqueued: {response.name} (correlation_id: {correlation_id}, payload_size: {payload_size})")

    return response.name

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """GitHub webhook endpoint - Airlock pattern."""
    start_time = time.time()

    # SECURITY: Verify signature FIRST
    signature_header = request.headers.get('X-Hub-Signature-256')

    if not verify_github_signature(request.data, signature_header):
        logger.warning("POST /webhook/github rejected: invalid or missing signature")
        abort(401)

    # Get delivery ID
    delivery_id = request.headers.get('X-GitHub-Delivery')
    if not delivery_id:
        logger.warning("POST /webhook/github rejected: missing X-GitHub-Delivery header")
        abort(400)

    # Idempotency check
    if not check_idempotency(delivery_id, source='github'):
        logger.info(f"POST /webhook/github duplicate skipped (delivery_id: {delivery_id})")
        return jsonify({'status': 'duplicate'}), 202

    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse JSON payload: {e}")
        return jsonify({'status': 'error', 'reason': 'invalid_json'}), 202

    # Filter events: only handle issue_comment
    event_type = request.headers.get('X-GitHub-Event')

    if event_type != 'issue_comment':
        logger.info(f"POST /webhook/github ignored: event={event_type}")
        return jsonify({'status': 'ignored', 'reason': 'event_type'}), 202

    # Filter action: only handle "created"
    action = payload.get('action')
    if action != 'created':
        logger.info(f"POST /webhook/github ignored: action={action}")
        return jsonify({'status': 'ignored', 'reason': 'action'}), 202

    # Build unified event structure
    correlation_id = f"gh_{delivery_id}_{int(time.time())}"

    event_data = {
        'source': 'github',
        'event_type': 'issue_comment.created',
        'correlation_id': correlation_id,
        'delivery_id': delivery_id,
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': {
            'installation_id': payload.get('installation', {}).get('id'),
            'repo_full_name': payload.get('repository', {}).get('full_name'),
            'repo_owner': payload.get('repository', {}).get('owner', {}).get('login'),
            'issue_number': payload.get('issue', {}).get('number'),
            'comment_id': payload.get('comment', {}).get('id'),
            'comment_user': payload.get('comment', {}).get('user', {}).get('login'),
            'comment_user_type': payload.get('comment', {}).get('user', {}).get('type'),
        },
        'payload': {
            'comment_body': payload.get('comment', {}).get('body', ''),
            'issue_title': payload.get('issue', {}).get('title', ''),
            'issue_labels': [l['name'] for l in payload.get('issue', {}).get('labels', [])]
        }
    }

    # Log metadata only (no bodies)
    logger.info(f"GitHub event: correlation_id={correlation_id} repo={event_data['metadata']['repo_full_name']} issue=#{event_data['metadata']['issue_number']} user={event_data['metadata']['comment_user']}")

    # Enqueue task
    try:
        task_name = enqueue_task(event_data, correlation_id)
        elapsed = int((time.time() - start_time) * 1000)

        logger.info(f"Airlock processed GitHub webhook in {elapsed}ms (task: {task_name})")

        return jsonify({
            'status': 'enqueued',
            'correlation_id': correlation_id,
            'task_name': task_name,
            'elapsed_ms': elapsed
        }), 202

    except Exception as e:
        logger.error(f"Failed to enqueue task: {e.__class__.__name__}")
        return jsonify({'status': 'error', 'reason': 'enqueue_failed'}), 202

@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Telegram webhook endpoint - Airlock pattern."""
    start_time = time.time()

    # SECURITY: Verify token (Telegram uses X-Telegram-Bot-Api-Secret-Token header)
    token_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')

    if not verify_telegram_token(token_header):
        logger.warning("POST /webhook/telegram rejected: invalid or missing token")
        abort(401)

    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse Telegram JSON payload: {e}")
        return jsonify({'status': 'error', 'reason': 'invalid_json'}), 202

    # Get update_id for idempotency
    update_id = payload.get('update_id')
    if not update_id:
        logger.warning("POST /webhook/telegram rejected: missing update_id")
        abort(400)

    # Idempotency check
    if not check_idempotency(str(update_id), source='telegram'):
        logger.info(f"POST /webhook/telegram duplicate skipped (update_id: {update_id})")
        return jsonify({'status': 'duplicate'}), 202

    # Build unified event structure
    correlation_id = f"tg_{update_id}_{int(time.time())}"

    message = payload.get('message', {})

    event_data = {
        'source': 'telegram',
        'event_type': 'message',
        'correlation_id': correlation_id,
        'delivery_id': str(update_id),
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': {
            'update_id': update_id,
            'chat_id': message.get('chat', {}).get('id'),
            'user_id': message.get('from', {}).get('id'),
            'username': message.get('from', {}).get('username'),
            'first_name': message.get('from', {}).get('first_name'),
        },
        'payload': {
            'message_text': message.get('text', ''),
            'message_id': message.get('message_id'),
        }
    }

    # Log metadata only
    logger.info(f"Telegram event: correlation_id={correlation_id} chat_id={event_data['metadata']['chat_id']} user={event_data['metadata']['username']}")

    # Enqueue task
    try:
        task_name = enqueue_task(event_data, correlation_id)
        elapsed = int((time.time() - start_time) * 1000)

        logger.info(f"Airlock processed Telegram webhook in {elapsed}ms (task: {task_name})")

        return jsonify({
            'status': 'enqueued',
            'correlation_id': correlation_id,
            'task_name': task_name,
            'elapsed_ms': elapsed
        }), 202

    except Exception as e:
        logger.error(f"Failed to enqueue Telegram task: {e.__class__.__name__}")
        return jsonify({'status': 'error', 'reason': 'enqueue_failed'}), 202

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'service': 'airlock'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
