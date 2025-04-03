from fastapi import APIRouter
from starlette.responses import JSONResponse

from utils.db_utils import get_capstone_db_connection
from utils.gpt_utils import gpt_call

test_router = APIRouter()

@test_router.get("/db")
def test_db():
    """
        DB 연결을 확인하는 API입니다.
    """
    try:
        conn = get_capstone_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
        conn.close()
        return JSONResponse(
            content={"message": "Database connection successful"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"message": "Database connection failed", "error": str(e)},
            status_code=500
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
            status_code=200
        )
    except Exception as e:
        # return {"message": "GPT 호출 실패", "error": str(e)}, 500
        return JSONResponse(
            content={
                "message": "GPT 호출 실패",
                "error": str(e)
            },
            status_code=500
        )