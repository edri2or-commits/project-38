import os
import hmac
import hashlib
import logging
from flask import Flask, request, abort

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    # Extract delivery ID for logging (GitHub sends X-GitHub-Delivery header)
    delivery_id = request.headers.get('X-GitHub-Delivery', 'unknown')
    
    # Get signature header
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    # Verify signature
    if not verify_signature(request.data, signature_header):
        # Log rejection (no headers/body, only delivery_id)
        logger.warning(f"POST /webhook rejected: invalid signature (delivery_id: {delivery_id})")
        abort(401)  # Unauthorized
    
    # Log successful verification (no headers/body, only delivery_id)
    logger.info(f"POST /webhook received (delivery_id: {delivery_id})")
    
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
