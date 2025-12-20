import os
import hmac
import hashlib
import logging
import time
import jwt
import requests
from datetime import datetime, timedelta
from flask import Flask, request, abort
from google.cloud import firestore
from google.cloud.exceptions import Conflict
from google.cloud import secretmanager

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

# Load configuration from environment
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID')
GITHUB_APP_PRIVATE_KEY_SECRET = os.environ.get('GITHUB_APP_PRIVATE_KEY_SECRET')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'project-38-ai')

if not WEBHOOK_SECRET:
    logger.error("WEBHOOK_SECRET environment variable not set")
    raise ValueError("WEBHOOK_SECRET must be configured")

if not GITHUB_APP_ID:
    logger.error("GITHUB_APP_ID environment variable not set")
    raise ValueError("GITHUB_APP_ID must be configured")

if not GITHUB_APP_PRIVATE_KEY_SECRET:
    logger.error("GITHUB_APP_PRIVATE_KEY_SECRET environment variable not set")
    raise ValueError("GITHUB_APP_PRIVATE_KEY_SECRET must be configured")

# Initialize Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

def get_github_app_private_key():
    """Retrieve GitHub App private key from Secret Manager."""
    try:
        name = f"projects/{GCP_PROJECT_ID}/secrets/{GITHUB_APP_PRIVATE_KEY_SECRET}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Failed to retrieve private key from Secret Manager: {e}")
        raise

def generate_app_jwt():
    """Generate GitHub App JWT for authentication."""
    private_key = get_github_app_private_key()
    
    payload = {
        'iat': int(time.time()) - 60,  # Issued at (1 min ago for clock drift)
        'exp': int(time.time()) + 600,  # Expires in 10 minutes
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
    
    try:
        response = requests.post(url, headers=headers, timeout=2)
        response.raise_for_status()
        return response.json()['token']
    except Exception as e:
        logger.error(f"Failed to get installation token: {e}")
        raise

def post_ack_comment(installation_id, repo_full_name, issue_number, comment_id, delivery_id):
    """Post ACK comment to the issue."""
    try:
        # Get installation access token
        token = get_installation_access_token(installation_id)
        
        # Prepare comment body
        comment_body = f"ACK: received comment_id={comment_id} delivery_id={delivery_id}"
        
        # Post comment
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        url = f'https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments'
        payload = {'body': comment_body}
        
        response = requests.post(url, headers=headers, json=payload, timeout=2)
        response.raise_for_status()
        
        ack_comment_id = response.json()['id']
        logger.info(f"ACK posted: comment_id={ack_comment_id} for issue #{issue_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to post ACK comment: {e}")
        return False

def verify_signature(payload_body, signature_header):
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

@app.route('/webhook', methods=['POST'])
def webhook():
    # SECURITY: Verify signature FIRST
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    if not verify_signature(request.data, signature_header):
        logger.warning("POST /webhook rejected: invalid or missing signature")
        abort(401)
    
    # Get delivery ID
    delivery_id = request.headers.get('X-GitHub-Delivery')
    if not delivery_id:
        logger.warning("POST /webhook rejected: missing X-GitHub-Delivery header")
        abort(400)
    
    # Idempotency check
    doc_ref = db.collection('webhook_deliveries').document(delivery_id)
    
    try:
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'seen',
            'expireAt': datetime.utcnow() + timedelta(days=1)
        })
        
        logger.info(f"POST /webhook processing (delivery_id: {delivery_id})")
        
    except Conflict:
        logger.info(f"POST /webhook duplicate skipped (delivery_id: {delivery_id})")
        return 'Accepted', 202
    
    # Filter events: only handle issue_comment
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type != 'issue_comment':
        logger.info(f"POST /webhook ignored: event={event_type}")
        return 'Accepted', 202
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse JSON payload: {e}")
        return 'Accepted', 202
    
    # Filter action: only handle "created"
    action = payload.get('action')
    if action != 'created':
        logger.info(f"POST /webhook ignored: action={action}")
        return 'Accepted', 202
    
    # Guard against loops: if comment starts with "ACK:", skip
    comment_body = payload.get('comment', {}).get('body', '')
    if comment_body.startswith('ACK:'):
        logger.info("POST /webhook ignored: ACK comment (loop guard)")
        return 'Accepted', 202
    
    # Extract required fields
    installation_id = payload.get('installation', {}).get('id')
    repo_full_name = payload.get('repository', {}).get('full_name')
    issue_number = payload.get('issue', {}).get('number')
    comment_id = payload.get('comment', {}).get('id')
    
    # Log metadata only (no bodies)
    logger.info(f"issue_comment.created: installation_id={installation_id} repo={repo_full_name} issue=#{issue_number} comment_id={comment_id}")
    
    if not all([installation_id, repo_full_name, issue_number, comment_id]):
        logger.error("Missing required fields in payload")
        return 'Accepted', 202
    
    # Post ACK comment (best-effort with timeout)
    # Return 202 immediately regardless of success
    post_ack_comment(installation_id, repo_full_name, issue_number, comment_id, delivery_id)
    
    return 'Accepted', 202

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
