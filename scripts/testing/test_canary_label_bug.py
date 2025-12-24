#!/usr/bin/env python3
"""Test /label bug command on canary revision"""
import hashlib
import hmac
import json
import requests
import uuid
from datetime import datetime

# Configuration
CANARY_URL = "https://canary---github-webhook-receiver-u7gbgdjoja-uc.a.run.app/webhook"
WEBHOOK_SECRET = "vw7Ou9LZKytNmaSGQn4Dp2dgVYsPx1I3"
DELIVERY_ID = str(uuid.uuid4())

# Payload
payload = {
    "action": "created",
    "issue": {
        "number": 18,
        "html_url": "https://github.com/edri2or-commits/project-38/issues/18"
    },
    "comment": {
        "id": 9999003,  # Test comment ID
        "user": {
            "login": "edri2or-commits",
            "type": "User"
        },
        "body": "/label bug"
    },
    "repository": {
        "full_name": "edri2or-commits/project-38",
        "owner": {
            "login": "edri2or-commits"
        }
    },
    "installation": {
        "id": 100231961
    }
}

payload_bytes = json.dumps(payload).encode('utf-8')

# Generate signature
mac = hmac.new(
    WEBHOOK_SECRET.encode('utf-8'),
    msg=payload_bytes,
    digestmod=hashlib.sha256
)
signature = f"sha256={mac.hexdigest()}"

# Headers
headers = {
    'Content-Type': 'application/json',
    'X-GitHub-Event': 'issue_comment',
    'X-GitHub-Delivery': DELIVERY_ID,
    'X-Hub-Signature-256': signature,
    'User-Agent': 'GitHub-Hookshot/test'
}

# Send request
print(f"[{datetime.now().isoformat()}] Sending POST to canary")
print(f"Delivery-ID: {DELIVERY_ID}")
print(f"Command: /label bug")
print(f"URL: {CANARY_URL}")
print()

response = requests.post(CANARY_URL, headers=headers, data=payload_bytes, timeout=10)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print()
print(f"Test sent - Delivery-ID: {DELIVERY_ID}")
print(f"Check issue #18 for 'bug' label")
