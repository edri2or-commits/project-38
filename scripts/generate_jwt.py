import jwt
import time
import sys

# Read private key
with open(sys.argv[1], 'r') as f:
    private_key = f.read()

# Generate JWT
now = int(time.time())
payload = {
    'iat': now,
    'exp': now + (10 * 60),  # 10 minutes
    'iss': '2497877'  # GitHub App ID
}

token = jwt.encode(payload, private_key, algorithm='RS256')
print(token)
