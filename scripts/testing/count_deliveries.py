import jwt
import time
import requests

# Generate JWT
with open(r"C:\Users\edri2\project-38-scribe.2025-12-18.private-key.pem", "r") as f:
    private_key = f.read()

payload = {
    'iat': int(time.time()) - 60,
    'exp': int(time.time()) + 600,
    'iss': '2497877'
}

app_jwt = jwt.encode(payload, private_key, algorithm='RS256')

# Get deliveries
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {app_jwt}',
    'X-GitHub-Api-Version': '2022-11-28'
}

response = requests.get('https://api.github.com/app/hook/deliveries?per_page=10', headers=headers)
deliveries = response.json()

# Filter issue_comment since test
recent = [d for d in deliveries if d.get('event') == 'issue_comment' and d.get('delivered_at', '') >= '2025-12-20T00:00:00Z']

print(f"Total issue_comment deliveries since 00:00:00Z: {len(recent)}")
for d in recent:
    print(f"  - {d['guid']}: {d['delivered_at']}")
