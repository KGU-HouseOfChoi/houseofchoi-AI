import os

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))

def get_redis_client() -> redis.Redis:
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)