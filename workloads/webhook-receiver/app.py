import os
import logging
from flask import Flask, request

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Extract delivery ID if present (GitHub sends X-GitHub-Delivery header)
    delivery_id = request.headers.get('X-GitHub-Delivery', 'unknown')
    
    # Log ONLY that request was received + delivery ID
    # DO NOT log headers, body, or any other request data
    logger.info(f"POST /webhook received (delivery_id: {delivery_id})")
    
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
