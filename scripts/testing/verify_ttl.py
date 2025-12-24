#!/usr/bin/env python3
"""Verify TTL field in webhook_deliveries collection."""

from google.cloud import firestore
from datetime import datetime

db = firestore.Client(project='project-38-ai')

# Get recent document
docs = list(db.collection('webhook_deliveries').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).stream())

if not docs:
    print("No documents found")
else:
    doc = docs[0]
    data = doc.to_dict()
    
    print(f"Document ID: {doc.id}")
    print(f"\nFields:")
    print(f"  timestamp: {data.get('timestamp')}")
    print(f"  status: {data.get('status')}")
    print(f"  expireAt: {data.get('expireAt')}")
    
    # Verify expireAt is set and is datetime
    expire_at = data.get('expireAt')
    if expire_at:
        if isinstance(expire_at, datetime):
            print(f"\n✅ TTL-2 PASS: expireAt field exists and is datetime")
            print(f"   Expires: {expire_at}")
        else:
            print(f"\n❌ TTL-2 FAIL: expireAt exists but wrong type: {type(expire_at)}")
    else:
        print(f"\n❌ TTL-2 FAIL: expireAt field missing")
