import os
from fastapi import Request, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM  = os.getenv("JWT_ALGORITHM")
ISSUER     = os.getenv("JWT_ISSUER")


def verify_token(request: Request) -> str:
    """
    HttpOnly 쿠키 'AccessToken'만 읽어 JWT 검증.
    통과하면 payload['sub'](user_id) 반환
    """
    token = request.cookies.get("AccessToken")
    if not token:
        raise HTTPException(status_code=401, detail="AccessToken 쿠키가 없습니다")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("iss") != ISSUER:
            raise HTTPException(status_code=401, detail="잘못된 토큰 발급자")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="payload에 sub 없음")

        return user_id

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 만료")
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")
