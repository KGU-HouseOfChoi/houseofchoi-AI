import requests
from redis import Redis
from fastapi import APIRouter, status, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from crud.schedule import create_schedule
from crud.user import get_user_by_id
from crud.program import get_program_by_id
from crud.schedule import create_schedule
from schemas.test_schema import ScheduleCreateRequest
from utils.database import get_db
from utils.gpt_utils import gpt_call
from utils.redis_utils import get_redis_client
from utils.stt_utils import fetch_token_from_return_zero, try_stt
from utils.jwt_utils import verify_token

test_router = APIRouter(prefix="/test", tags=["test"])


# ────────────────────────────────────────────────
# DB 연결 확인
# ────────────────────────────────────────────────
@test_router.get("/db")
def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return JSONResponse(
                {"message": "Database connection successful"}, status_code=status.HTTP_200_OK
            )
        raise Exception("Failed to execute test query")
    except Exception as e:
        return JSONResponse(
            {"message": "Database connection failed", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ────────────────────────────────────────────────
# GPT 챗봇 테스트 (쿠키 인증)
# ────────────────────────────────────────────────
@test_router.post("/chatbot")
def chatbot_test(user_id: str = Depends(verify_token)):
    """
    쿠키 AccessToken → user_id 추출
    """
    try:
        system_prompt = "당신은 친절한 AI 비서입니다."
        response_text = gpt_call(system_prompt, "안녕하세요 반가워요!")

        return {
            "message": "야로밥라니",
            "user_id": user_id,
            "response": response_text,
        }
    except Exception as e:
        raise HTTPException(500, detail=f"GPT 호출 실패: {e}")


# ────────────────────────────────────────────────
# 테스트용 일정 저장
# ────────────────────────────────────────────────
@test_router.post("/save/schedule")
def create_schedule_for_test(
    request: ScheduleCreateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token),
):
    """
    body: { "program_id": ...,  "user_id": ... }  ←  body.user_id는 dev 편의용
    실제 인증은 쿠키 AccessToken으로 처리
    """
    if str(request.user_id) != str(user_id):
        return JSONResponse(
            {"error": "body.user_id와 쿠키 user_id가 일치하지 않습니다."},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    user = get_user_by_id(db, request.user_id)
    program = get_program_by_id(db, request.program_id)
    schedule = create_schedule(db=db, user=user, program=program, center=program.center)

    return {"message": "Schedule created successfully", "schedule_id": schedule.id}


# ────────────────────────────────────────────────
# Redis 연결 확인
# ────────────────────────────────────────────────
@test_router.get("/redis")
def test_redis(redis: Redis = Depends(get_redis_client)):
    try:
        redis.set("test", "어르심")
        redis.getdel("test")
        return JSONResponse({"result": "redis connection successful"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            {"message": "redis connection failed", "error": str(e)}, status_code=500
        )


# ────────────────────────────────────────────────
# ReturnZero STT 토큰
# ────────────────────────────────────────────────
@test_router.get("/stt-token")
def get_stt_token(
    redis: Redis = Depends(get_redis_client),
    user_id: str = Depends(verify_token),
):
    try:
        token = fetch_token_from_return_zero(redis)
        return token
    except Exception as e:
        return JSONResponse({"message": "get token failed", "error": str(e)}, status_code=500)


# ────────────────────────────────────────────────
# STT 테스트
# ────────────────────────────────────────────────
@test_router.post("/stt")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    redis: Redis = Depends(get_redis_client),
    user_id: str = Depends(verify_token),
):
    try:
        result = await try_stt(audio_file, redis)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
