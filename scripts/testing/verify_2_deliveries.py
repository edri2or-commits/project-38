import jwt
import time
import requests
import json

app_id = "2497877"

with open(r'C:\Users\edri2\project-38-scribe.2025-12-18.private-key.pem', 'r') as f:
    private_key = f.read()

payload = {
    'iat': int(time.time()) - 60,
    'exp': int(time.time()) + 600,
    'iss': app_id
}

token = jwt.encode(payload, private_key, algorithm='RS256')

headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {token}',
    'X-GitHub-Api-Version': '2022-11-28'
}

response = requests.get(
    'https://api.github.com/app/hook/deliveries?per_page=10',
    headers=headers
)

print(json.dumps(response.json(), indent=2))
