import os
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Flask, request, abort
from google.cloud import firestore
from google.api_core.exceptions import AlreadyExists

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Firestore client
db = firestore.Client()

# Load webhook secret from environment
# In production, this should be injected from Secret Manager
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
if not WEBHOOK_SECRET:
    logger.error("WEBHOOK_SECRET environment variable not set")
    raise ValueError("WEBHOOK_SECRET must be configured")

def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload_body: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature_header:
        return False
    
    # GitHub sends signature in format: "sha256=<hexdigest>"
    try:
        hash_algorithm, github_signature = signature_header.split('=', 1)
    except ValueError:
        return False
    
    if hash_algorithm != 'sha256':
        return False
    
    # Compute expected signature
    mac = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()
    
    # Timing-safe comparison (mitigates timing attacks)
    return hmac.compare_digest(expected_signature, github_signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Extract delivery ID for logging and idempotency
    delivery_id = request.headers.get('X-GitHub-Delivery')
    
    if not delivery_id:
        logger.warning("POST /webhook rejected: missing X-GitHub-Delivery header")
        abort(400)
    
    # Idempotency check: Atomic create in Firestore
    # Uses document create() which fails if document already exists
    doc_ref = db.collection('webhook_deliveries').document(delivery_id)
    
    try:
        # Atomic operation: create document with TTL field
        # If document exists, this will raise AlreadyExists
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'seen',
            'expireAt': datetime.utcnow() + timedelta(days=1)
        })
        
        # Document created successfully - first time seeing this delivery
        logger.info(f"POST /webhook processing (delivery_id: {delivery_id})")
        
    except AlreadyExists:
        # Document already exists - duplicate delivery
        logger.info(f"POST /webhook duplicate skipped (delivery_id: {delivery_id})")
        return 'Accepted', 202
    
    # Get signature header
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    # Verify signature
    if not verify_signature(request.data, signature_header):
        # Log rejection (no headers/body, only delivery_id)
        logger.warning(f"POST /webhook rejected: invalid signature (delivery_id: {delivery_id})")
        abort(401)  # Unauthorized
    
    # Signature verified - webhook accepted
    logger.info(f"POST /webhook accepted (delivery_id: {delivery_id})")
    
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
