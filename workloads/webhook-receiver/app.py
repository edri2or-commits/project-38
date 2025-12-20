import os
import hmac
import hashlib
import logging
import time
import jwt
import requests
from datetime import datetime, timedelta
from flask import Flask, request, abort, jsonify
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

def parse_command(comment_body):
    """
    Parse issue comment for commands.
    
    Returns:
        tuple: (command, args) or (None, None)
        
    Examples:
        "/label bug" → ("label", ["bug"])
        "/assign @user" → ("assign", ["user"])
        "regular comment" → (None, None)
    """
    if not comment_body.strip().startswith('/'):
        return None, None
    
    parts = comment_body.strip().split(maxsplit=1)
    command = parts[0][1:]  # Remove leading '/'
    args = parts[1].split() if len(parts) > 1 else []
    
    # Remove @ prefix from usernames
    if command == 'assign':
        args = [arg.lstrip('@') for arg in args]
    
    return command, args

def post_comment(installation_token, repo_full_name, issue_number, comment_body):
    """
    Post a comment to a GitHub issue.
    
    Args:
        installation_token: GitHub installation access token
        repo_full_name: Repository in format "owner/repo"
        issue_number: Issue number
        comment_body: Comment text to post
        
    Returns:
        dict: GitHub API response with comment details
        
    Raises:
        requests.HTTPError: If API request fails
    """
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {installation_token}',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    url = f'https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments'
    payload = {'body': comment_body}
    
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    response.raise_for_status()
    
    return response.json()

def add_label(installation_token, repo_full_name, issue_number, labels):
    """
    Add labels to issue via GitHub REST API.
    POST /repos/{owner}/{repo}/issues/{issue_number}/labels
    
    Docs: https://docs.github.com/en/rest/issues/labels#add-labels-to-an-issue
    
    Args:
        installation_token: GitHub installation access token
        repo_full_name: Repository in format "owner/repo"
        issue_number: Issue number
        labels: List of label names to add
        
    Returns:
        list: Updated list of all labels on the issue
        
    Raises:
        requests.HTTPError: If API request fails
    """
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/labels"
    headers = {
        'Authorization': f'Bearer {installation_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    payload = {"labels": labels}
    
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()

def assign_users(installation_token, repo_full_name, issue_number, assignees):
    """
    Assign users to issue via GitHub REST API.
    POST /repos/{owner}/{repo}/issues/{issue_number}/assignees
    
    Max 10 assignees. Users without push access may be ignored.
    Docs: https://docs.github.com/en/rest/issues/assignees#add-assignees-to-an-issue
    
    Args:
        installation_token: GitHub installation access token
        repo_full_name: Repository in format "owner/repo"
        issue_number: Issue number
        assignees: List of usernames to assign (max 10)
        
    Returns:
        dict: Updated issue object
        
    Raises:
        requests.HTTPError: If API request fails
    """
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/assignees"
    headers = {
        'Authorization': f'Bearer {installation_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    payload = {"assignees": assignees[:10]}  # Max 10
    
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()

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
        return jsonify({'status': 'duplicate'}), 202
    
    # Filter events: only handle issue_comment
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type != 'issue_comment':
        logger.info(f"POST /webhook ignored: event={event_type}")
        return jsonify({'status': 'ignored', 'reason': 'event_type'}), 202
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse JSON payload: {e}")
        return jsonify({'status': 'error', 'reason': 'invalid_json'}), 202
    
    # Filter action: only handle "created"
    action = payload.get('action')
    if action != 'created':
        logger.info(f"POST /webhook ignored: action={action}")
        return jsonify({'status': 'ignored', 'reason': 'action'}), 202
    
    # Extract required fields
    installation_id = payload.get('installation', {}).get('id')
    repo_full_name = payload.get('repository', {}).get('full_name')
    repo_owner = payload.get('repository', {}).get('owner', {}).get('login')
    issue_number = payload.get('issue', {}).get('number')
    comment_id = payload.get('comment', {}).get('id')
    comment_user = payload.get('comment', {}).get('user', {}).get('login')
    comment_user_type = payload.get('comment', {}).get('user', {}).get('type')
    comment_body = payload.get('comment', {}).get('body', '')
    
    # Log metadata only (no bodies)
    logger.info(f"issue_comment.created: installation_id={installation_id} repo={repo_full_name} issue=#{issue_number} comment_id={comment_id} user={comment_user} user_type={comment_user_type}")
    
    if not all([installation_id, repo_full_name, repo_owner, issue_number, comment_id, comment_user]):
        logger.error("Missing required fields in payload")
        return jsonify({'status': 'error', 'reason': 'missing_fields'}), 202
    
    # BOT GUARD: Ignore comments from Bot users to prevent loops
    if comment_user_type == 'Bot':
        logger.info(f"POST /webhook ignored: bot user={comment_user}")
        return jsonify({'status': 'ignored', 'reason': 'bot_user'}), 202
    
    # PARSE BEFORE AUTH: Check if this is a command
    command, args = parse_command(comment_body)
    
    # If not a command, post ACK and return (legacy behavior)
    if command is None:
        try:
            installation_token = get_installation_access_token(installation_id)
            ack_body = f"ACK: received comment_id={comment_id} delivery_id={delivery_id}"
            result = post_comment(installation_token, repo_full_name, issue_number, ack_body)
            logger.info(f"ACK posted: comment_id={result['id']} for issue #{issue_number}")
            return jsonify({'status': 'ack_posted', 'comment_id': result['id']}), 202
        except Exception as e:
            logger.error(f"Failed to post ACK: {e.__class__.__name__}")
            return jsonify({'status': 'error', 'reason': 'ack_failed'}), 202
    
    # SECURITY: Owner-only commands
    if comment_user != repo_owner:
        logger.warning(f"Unauthorized command attempt: user={comment_user} owner={repo_owner} command=/{command}")
        return jsonify({'status': 'unauthorized', 'reason': 'not_owner'}), 202
    
    # Get installation token for command execution
    try:
        installation_token = get_installation_access_token(installation_id)
    except Exception as e:
        logger.error(f"Failed to get installation token: {e.__class__.__name__}")
        try:
            # Best-effort error comment
            post_comment(installation_token, repo_full_name, issue_number, f"❌ Internal error: failed to authenticate")
        except:
            pass
        return jsonify({'status': 'error', 'reason': 'auth_failed'}), 202
    
    # Execute command
    try:
        if command == 'label':
            if not args:
                post_comment(installation_token, repo_full_name, issue_number, "❌ Usage: `/label <label_name>`")
                return jsonify({'status': 'error', 'reason': 'missing_args'}), 202
            
            add_label(installation_token, repo_full_name, issue_number, args)
            post_comment(installation_token, repo_full_name, issue_number, f"✅ Label(s) added: `{', '.join(args)}`")
            logger.info(f"Command executed: /label {args} on issue #{issue_number}")
            return jsonify({'status': 'command_executed', 'command': 'label', 'args': args}), 202
            
        elif command == 'assign':
            if not args:
                post_comment(installation_token, repo_full_name, issue_number, "❌ Usage: `/assign @username`")
                return jsonify({'status': 'error', 'reason': 'missing_args'}), 202
            
            assign_users(installation_token, repo_full_name, issue_number, args)
            post_comment(installation_token, repo_full_name, issue_number, f"✅ Assigned: `{', '.join(args)}`")
            logger.info(f"Command executed: /assign {args} on issue #{issue_number}")
            return jsonify({'status': 'command_executed', 'command': 'assign', 'args': args}), 202
            
        else:
            post_comment(installation_token, repo_full_name, issue_number, f"❌ Unknown command: `/{command}`")
            logger.info(f"Unknown command: /{command} args={args}")
            return jsonify({'status': 'unknown_command', 'command': command}), 202
            
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response else 'unknown'
        logger.error(f"GitHub API error: command=/{command} status={status_code}")
        try:
            post_comment(installation_token, repo_full_name, issue_number, f"❌ Failed to execute `/{command}`: API error {status_code}")
        except:
            pass
        return jsonify({'status': 'api_error', 'command': command, 'http_status': status_code}), 202
    except Exception as e:
        logger.error(f"Command execution error: command=/{command} error={e.__class__.__name__}")
        try:
            post_comment(installation_token, repo_full_name, issue_number, f"❌ Failed to execute `/{command}`: internal error")
        except:
            pass
        return jsonify({'status': 'error', 'command': command}), 202

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
