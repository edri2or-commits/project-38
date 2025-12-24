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
