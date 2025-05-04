import requests
from redis import Redis
from fastapi import APIRouter, status, File, UploadFile
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from crud.schedule import create_schedule
from schemas.test_schema import ScheduleCreateRequest
from utils.database import get_db
from utils.gpt_utils import gpt_call

from crud.user import get_user_by_id
from crud.program import get_program_by_id
from utils.redis_utils import get_redis_client
from utils.stt_utils import fetch_token_from_return_zero, try_stt

test_router = APIRouter()

@test_router.get("/db")
def test_db(db: Session = Depends(get_db)):
    """
        DB 연결을 확인하는 API입니다.
    """
    try:
        # DB에서 단순 쿼리 실행하여 연결 확인
        result = db.execute(text('SELECT 1'))
        if result.scalar() == 1:
            return JSONResponse(
                content={"message": "Database connection successful"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise Exception("Failed to execute test query")
    except Exception as e:
        return JSONResponse(
            content={"message": "Database connection failed", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@test_router.post("/chatbot")
def chatbot_test():
    """
    OpenAI GPT 챗봇 테스트 API
    """
    try:
        user_prompt = "안녕하세요 반가워요!"

        system_prompt = "당신은 친절한 AI 비서입니다."
        response_text = gpt_call(system_prompt, user_prompt)

        return JSONResponse(
            content={
                "message": "GPT 응답 성공",
                "response": response_text
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        # return {"message": "GPT 호출 실패", "error": str(e)}, 500
        return JSONResponse(
            content={
                "message": "GPT 호출 실패",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@test_router.post("/save/schedule")
def create_schedule_for_test(request: ScheduleCreateRequest, db: Session = Depends(get_db)):
    print("request:", request)
    user = get_user_by_id(db, request.user_id)

    program = get_program_by_id(db, request.program_id)

    schedule = create_schedule(db=db, user=user, program=program, center=program.center)

    return {"message": "Schedule created successfully", "schedule_id": schedule.id}

@test_router.get("/redis")
def test_redis(redis: Redis = Depends(get_redis_client)):
    try:
        redis.set("test", "어르심")
        redis.getdel("test")
        return JSONResponse(
            content={
                "result":"redis connection successful",
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "message": "redis connection failed",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@test_router.get("/stt-token")
def get_stt_token(redis: Redis=Depends(get_redis_client)):
    try:
        token = fetch_token_from_return_zero(redis)
        return JSONResponse(
            content=token,
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "message": "get token failed",
                "error": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@test_router.post("/stt")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    redis: Redis = Depends(get_redis_client)
):
    try:
        result = await try_stt(audio_file, redis)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})