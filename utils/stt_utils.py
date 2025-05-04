import os
import requests
from dotenv import load_dotenv
from redis import Redis

load_dotenv()

RETURN_ZERO_CLIENT = os.getenv('RETURN_ZERO_CLIENT')
RETURN_ZERO_SECRET = os.getenv('RETURN_ZERO_SECRET')
RETURN_ZERO_JWT_URL = os.getenv('RETURN_ZERO_JWT_URL')
RETURN_ZERO_TOKEN_KEY = os.getenv('RETURN_ZERO_TOKEN_KEY')

def fetch_token_from_return_zero(redis: Redis) -> str:
    if redis.exists(RETURN_ZERO_TOKEN_KEY):
        print(f'redis cache hit => key : {RETURN_ZERO_TOKEN_KEY}, value {redis.get(RETURN_ZERO_TOKEN_KEY)}')
        return redis.get(RETURN_ZERO_TOKEN_KEY)

    data = {
        "client_id": RETURN_ZERO_CLIENT,
        "client_secret": RETURN_ZERO_SECRET
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(RETURN_ZERO_JWT_URL, headers=headers, data=data)

    token_data = response.json()

    token = token_data["access_token"]
    print(f'token: {token}')
    redis.setex(RETURN_ZERO_TOKEN_KEY, 60*60*6, token)

    return token