# utils/jwt_utils.py
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError


# 🔐 Swagger 에 securityScheme 를 자동 등록해 주는 Bearer 스킴
bearer_scheme = HTTPBearer(auto_error=True)

SECRET_KEY = os.getenv("JWT_SECRET")      # ❗기본값 제거
ALGORITHM  = os.getenv("JWT_ALGORITHM")
ISSUER     = os.getenv("JWT_ISSUER")

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """
    - Swagger 의 전역 Authorize 로 입력한 Bearer 토큰을 자동 주입받음
    - 검증 통과 시 payload['sub'](user_id) 리턴
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("iss") != ISSUER:
            raise HTTPException(status_code=401, detail="Invalid token issuer")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="user_id(sub) 누락")
        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
