import os
import time
from typing import Any, Coroutine

import requests
from fastapi import UploadFile
from dotenv import load_dotenv
from redis import Redis

load_dotenv()

RETURN_ZERO_CLIENT = os.getenv('RETURN_ZERO_CLIENT')
RETURN_ZERO_SECRET = os.getenv('RETURN_ZERO_SECRET')
RETURN_ZERO_URL = os.getenv('RETURN_ZERO_URL')
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

async def try_stt(audio_file: UploadFile, redis: Redis) -> str | None | Any:
    # 토큰 가져오기 (레디스 캐시 활용)
    token = fetch_token_from_return_zero(redis)
    if isinstance(token, bytes):
        token = token.decode()

    # 파일 바이트 읽기
    audio_bytes = await audio_file.read()

    # multipart/form-data 구성
    files = {
        "file": (audio_file.filename, audio_bytes, audio_file.content_type),
        "config": (None, '{"model_name": "whisper", "language": "ko"}')
    }

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # STT API 요청
    response = requests.post(RETURN_ZERO_URL, headers=headers, files=files)

    # 응답 결과 반환
    if response.status_code != 200:
        raise Exception(f"STT request failed: {response.status_code}, {response.text}")

    result = response.json()

    max_attempts = 30
    interval = 2

    for _ in range(max_attempts):
        stt_result_reponse = requests.get(
            'https://openapi.vito.ai/v1/transcribe/' + result["id"],
            headers={"Authorization": f"Bearer {token}"},
        )

        if stt_result_reponse.status_code != 200:
            raise Exception(f"STT request failed: {response.status_code}, {response.text}")

        stt_result = stt_result_reponse.json()

        if stt_result["status"] == "completed":
            utterances = stt_result.get("results", {}).get("utterances", [])
            if utterances:
                return utterances[0]["msg"]  # ✅ msg 값만 반환
            return ""
        elif stt_result["status"] == "failed":
            raise Exception(f"STT request failed: {response.status_code}, {response.text}")
        else:
            time.sleep(interval)