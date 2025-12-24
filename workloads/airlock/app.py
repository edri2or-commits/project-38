# POC-03: Airlock (Updated webhook-receiver)
# Telegram/GitHub → Airlock → Queue → Worker

import os
import hmac
import hashlib
import logging
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

# Load configuration
WEBHOOK_SECRET_GITHUB = os.environ.get('WEBHOOK_SECRET')
WEBHOOK_SECRET_TELEGRAM = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'project-38-ai')
QUEUE_NAME = 'issue-commands-queue'
QUEUE_LOCATION = 'us-central1'
WORKER_URL = os.environ.get('WORKER_URL')  # Cloud Run worker URL
BUCKET_NAME = f'{GCP_PROJECT_ID}-payloads'
PAYLOAD_SIZE_THRESHOLD = 100 * 1024  # 100KB

# Validation
if not WEBHOOK_SECRET_GITHUB:
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
        WEBHOOK_SECRET_GITHUB.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()
    
    return hmac.compare_digest(expected_signature, github_signature)

def verify_telegram_token(token_header):
    """Verify Telegram webhook token."""
    if not WEBHOOK_SECRET_TELEGRAM:
        return True  # Allow if not configured (for initial testing)
    
    return hmac.compare_digest(
        token_header or '',
        WEBHOOK_SECRET_TELEGRAM
    )

def store_payload_to_gcs(payload, correlation_id):
    """
    Store large payload to GCS and return claim-check reference.
    
    Returns:
        dict: {'type': 'gcs', 'bucket': ..., 'blob': ..., 'correlation_id': ...}
    """
    blob_name = f"payloads/{correlation_id}.json"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    
    blob.upload_from_string(
        json.dumps(payload),
        content_type='application/json'
    )
    
    logger.info(f"Payload stored to GCS: gs://{BUCKET_NAME}/{blob_name}")
    
    return {
        'type': 'gcs',
        'bucket': BUCKET_NAME,
        'blob': blob_name,
        'correlation_id': correlation_id
    }

def enqueue_task(payload, correlation_id, source):
    """
    Enqueue task to Cloud Tasks.
    
    Args:
        payload: Event payload (GitHub/Telegram)
        correlation_id: Unique ID for tracking
        source: 'github' or 'telegram'
    
    Returns:
        dict: Task response
    """
    queue_path = tasks_client.queue_path(
        GCP_PROJECT_ID,
        QUEUE_LOCATION,
        QUEUE_NAME
    )
    
    # Decide: inline or claim-check?
    payload_json = json.dumps(payload)
    payload_size = len(payload_json.encode('utf-8'))
    
    if payload_size > PAYLOAD_SIZE_THRESHOLD:
        # Large payload: use claim-check pattern
        logger.info(f"Payload size {payload_size} bytes exceeds threshold, using GCS claim-check")
        task_payload = store_payload_to_gcs(payload, correlation_id)
    else:
        # Small payload: inline
        task_payload = {
            'type': 'inline',
            'data': payload,
            'correlation_id': correlation_id
        }
    
    # Add metadata
    task_payload['source'] = source
    task_payload['enqueued_at'] = datetime.utcnow().isoformat()
    
    # Create task
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': WORKER_URL,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(task_payload).encode()
        }
    }
    
    response = tasks_client.create_task(
        request={
            'parent': queue_path,
            'task': task
        }
    )
    
    logger.info(f"Task enqueued: {response.name} (correlation_id={correlation_id})")
    
    return {
        'task_name': response.name,
        'correlation_id': correlation_id,
        'payload_type': task_payload['type']
    }

@app.route('/webhook', methods=['POST'])
def webhook_github():
    """GitHub webhook endpoint (issue_comment events)."""
    
    # SECURITY: Verify signature FIRST
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    if not verify_github_signature(request.data, signature_header):
        logger.warning("POST /webhook/github rejected: invalid signature")
        abort(401)
    
    # Get delivery ID
    delivery_id = request.headers.get('X-GitHub-Delivery')
    if not delivery_id:
        logger.warning("POST /webhook/github rejected: missing X-GitHub-Delivery")
        abort(400)
    
    # Idempotency check
    doc_ref = db.collection('webhook_deliveries').document(delivery_id)
    
    try:
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'seen',
            'source': 'github',
            'expireAt': datetime.utcnow() + timedelta(days=1)
        })
        
        logger.info(f"POST /webhook/github processing (delivery_id: {delivery_id})")
        
    except Conflict:
        logger.info(f"POST /webhook/github duplicate skipped (delivery_id: {delivery_id})")
        return jsonify({'status': 'duplicate', 'correlation_id': delivery_id}), 202
    
    # Filter events
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type != 'issue_comment':
        logger.info(f"POST /webhook/github ignored: event={event_type}")
        return jsonify({'status': 'ignored', 'reason': 'event_type'}), 202
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return jsonify({'status': 'error', 'reason': 'invalid_json'}), 202
    
    # Filter action
    action = payload.get('action')
    if action != 'created':
        logger.info(f"POST /webhook/github ignored: action={action}")
        return jsonify({'status': 'ignored', 'reason': 'action'}), 202
    
    # Enqueue to Cloud Tasks
    try:
        result = enqueue_task(payload, delivery_id, 'github')
        return jsonify({
            'status': 'enqueued',
            **result
        }), 202
    except Exception as e:
        logger.error(f"Failed to enqueue task: {e.__class__.__name__}")
        return jsonify({'status': 'error', 'reason': 'enqueue_failed'}), 202

@app.route('/webhook/telegram', methods=['POST'])
def webhook_telegram():
    """Telegram webhook endpoint."""
    
    # SECURITY: Verify token
    token_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    
    if not verify_telegram_token(token_header):
        logger.warning("POST /webhook/telegram rejected: invalid token")
        abort(401)
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse Telegram JSON: {e}")
        return jsonify({'status': 'error', 'reason': 'invalid_json'}), 202
    
    # Extract update_id for idempotency
    update_id = payload.get('update_id')
    if not update_id:
        logger.warning("POST /webhook/telegram rejected: missing update_id")
        abort(400)
    
    # Idempotency check
    correlation_id = f"telegram-{update_id}"
    doc_ref = db.collection('webhook_deliveries').document(correlation_id)
    
    try:
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'seen',
            'source': 'telegram',
            'update_id': update_id,
            'expireAt': datetime.utcnow() + timedelta(days=1)
        })
        
        logger.info(f"POST /webhook/telegram processing (update_id: {update_id})")
        
    except Conflict:
        logger.info(f"POST /webhook/telegram duplicate skipped (update_id: {update_id})")
        return jsonify({'status': 'duplicate', 'correlation_id': correlation_id}), 202
    
    # Enqueue to Cloud Tasks
    try:
        result = enqueue_task(payload, correlation_id, 'telegram')
        return jsonify({
            'status': 'enqueued',
            **result
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
