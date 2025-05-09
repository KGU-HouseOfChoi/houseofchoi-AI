from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Depends, File, Form
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy.orm import Session

from crud.chat_log import get_last_recommended_program_by_user_id, create_chat_log, create_chat_log_with_program, \
    get_chat_log_by_id
from crud.program import get_program_by_name
from crud.schedule import create_schedule
from crud.user import get_user_by_id
from schemas.chatlog_schema import ChatLogResponse
from utils.database import get_db
from utils.gpt_utils import gpt_call
from utils.chat_utils import (
    recommend_random_program,
    search_program_and_build_message,
    extract_requested_program,
)
from schemas.chatbot_schema import ChatbotRequest
from utils.redis_utils import get_redis_client
from utils.stt_utils import try_stt
from utils.jwt_utils import verify_token 

# API router
chat_router = APIRouter()


@chat_router.get("/log", response_model=List[ChatLogResponse])
def get_my_log(
    user_id: str = Depends(verify_token),     # JWT → user_id 추출
    db: Session = Depends(get_db)
):
    """
    내 대화 기록 조회 (JWT 토큰에서 user_id 추출)
    """
    return get_chat_log_by_id(db, user_id)


@chat_router.post("")
def chat_with_msg(
    body: ChatbotRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user_message = body.message
    chatbot_response = get_chatbot_response(user_id, user_message, db)

    return JSONResponse(
        status_code=200,
        content={
            "user_message": user_message,
            "chatbot_response": chatbot_response,
        },
    )


@chat_router.post("/record")
async def post_record(
    audio_file: Optional[UploadFile] = File(None),
    token_user_id: str = Depends(verify_token),       # 토큰 → user_id
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    """
    챗봇 STT API
    - user_id 는 JWT 토큰에서 자동 추출
    - audio_file : 녹음된 음성 파일
    """

    user_id = token_user_id          # 토큰 값을 그대로 사용

    # 🎙️ STT 처리
    try:
        user_message = await try_stt(audio_file, redis)
    except Exception as e:
        raise HTTPException(500, f"STT 변환 실패: {e}")

    # 🤖 챗봇 응답
    try:
        chatbot_response = get_chatbot_response(user_id, user_message, db)
    except Exception as e:
        raise HTTPException(500, f"챗봇 응답 생성 실패: {e}")

    return JSONResponse(
        status_code=200,
        content={
            "user_id": user_id,
            "user_message": user_message,
            "chatbot_response": chatbot_response,
        },
    )


def get_chatbot_response(user_id: str, user_message: str, db: Session):
    # (A) "예", "등록" 등으로 일정 등록 의사 표시
    if user_message.lower() in ["예", "네", "등록", "등록할래요"]:
        # 1) 최근 recommended_program 찾기 (프로그램명)
        recommended_program = get_last_recommended_program_by_user_id(user_id, db)
        if not recommended_program:
            raise HTTPException(
                status_code=400,
                detail="최근에 추천된 프로그램이 없습니다."
            )

        # 2) DB에서 해당 프로그램의 추가 정보를 조회 (요일1~요일5, 시작시간, 종료시간)
        print(recommended_program)
        program = get_program_by_name(db, recommended_program)
        user = get_user_by_id(db, int(user_id))

        # 3) schedule_route.py의 save_schedule 함수는 새 스키마에 맞춰 9개의 인자를 받으므로 호출
        schedule = create_schedule(
            db,
            user,
            program,
            program.center
        )

        if schedule:
            response_text = f"✅ '{recommended_program}' 일정이 등록되었습니다!"
            create_chat_log(db, user_id, user_message, response_text)
            return response_text
        else:
            raise HTTPException(
                status_code=500,
                detail="일정 등록 실패"
            )

    # (B) 사용자 메시지에서 프로그램명 추출
    requested_program = extract_requested_program(user_message)
    response = {"user_id": user_id}

    # (C-0) 대화 의도가 프로그램 추천과 무관할 경우 → 말벗 모드로 전환
    if requested_program is None:
        system_prompt = """
            다음 문장이 '복지 프로그램 추천을 요청하는 문장'인지 판단해 주세요.
            만약 추천 관련 요청이 아니고, 감성적인 말벗 대화나 일상적인 고민, 감정 표현이라면 '말벗'이라고만 답해주세요.
            예) '요즘 다리가 아파요' → 말벗
            예) '요가 수업 있어요?' → 추천
            """
        intent = gpt_call(system_prompt, user_message, max_tokens=10).strip().lower()

        if "말벗" in intent:
            # 감성적 말벗 응답
            system_prompt = """
                당신은 노인분들의 감정을 따뜻하게 받아주는 말벗입니다.
                사용자의 문장을 위로하거나 공감하는 따뜻한 한마디로 자연스럽게 응답해 주세요.
                너무 길지 않고 진심이 느껴지는 문장으로 부모님한테 하는 말처럼 만들어 주세요.
                예시:
                - '당신이 아프면 저도 가슴이 아파요.'
                - '마음이 많이 힘드셨겠어요. 제가 곁에 있을게요.'
                - '언제든지 편하게 이야기해 주세요. 전 늘 여기 있어요.'
                """
            assistant_answer = gpt_call(system_prompt, user_message)
            response["assistant_answer"] = assistant_answer
            chatbot_response = assistant_answer
            create_chat_log(db, user_id, user_message, chatbot_response)
            return chatbot_response

    # (C) 프로그램 추천 관련 처리
    if requested_program is None:
        # (C-1) 프로그램명이 언급되지 않았다면 => 무작위 추천
        # recommend_random_program 함수는 (안내문, 추천된 프로그램명) 두 값을 반환하도록 합니다.
        raw_msg, found_program_name = recommend_random_program(int(user_id), db)

        system_prompt = (
            "당신은 노인 복지 센터의 비서입니다. 아래 문장을 간단히 다듬어 주세요. "
            "주어진 프로그램 정보를 바탕으로, 친근하고 간결하며 자연스러운 문장으로 추천 메시지를 작성해 주세요. "
            "예시 형식: '서예교실을 추천드릴께요. 창의적이고 감성적인 당신께 잘 어울릴꺼에요... 등록하시겠습니까?' "
        )
        recommendation = gpt_call(system_prompt, raw_msg)
        response["recommendation"] = recommendation
        chatbot_response = recommendation

        # 무작위 추천한 프로그램명을 대화 로그에 기록 (found_program_name가 바로 저장됨)
        create_chat_log_with_program(db, user_id, user_message, chatbot_response, recommended_program=found_program_name)
        return chatbot_response

    else:
        # (C-2) 프로그램명이 언급되었다면 => DB 검색 또는 안내 메시지
        # search_program_and_build_message 함수는 (안내문, 추천된 프로그램명) 두 값을 반환하도록 합니다.
        raw_msg, found_program_name = search_program_and_build_message(db, requested_program)

        # 강제 문자열 변환: 혹시 raw_msg가 예상치 못한 타입일 경우를 대비
        if not isinstance(raw_msg, str):
            raw_msg = str(raw_msg)

        if found_program_name:
            system_prompt = (
                "당신은 노인 복지 센터 비서입니다. 친절히 안내해 주세요. "
                "친근하고 간결하며 자연스러운 문장으로 추천 메시지를 작성해 주세요. "
                "예시 형식: '네, 마침 SK청솔노인복지관에서 서예교실을 진행합니다... 등록하시겠습니까?' "
            )
            recommendation = gpt_call(system_prompt, raw_msg)
            response["recommendation"] = recommendation
            chatbot_response = recommendation
            response["recommended_program"] = found_program_name

            # 특정 프로그램명 언급 시에도 추천된 프로그램명을 대화 로그에 기록
            create_chat_log_with_program(db, user_id, user_message, chatbot_response, recommended_program=found_program_name)
            return chatbot_response

        else:
            system_prompt = (
                "짧고 부드러운 말투로 안내해 주세요. 죄송하지만 저희가 연계하고 있는 센터에는 "
                "그 프로그램이 없습니다로 시작해 주세요."
            )
            assistant_answer = gpt_call(system_prompt, raw_msg)
            response["assistant_answer"] = assistant_answer
            chatbot_response = assistant_answer
            # 이 경우 추천된 프로그램명이 없으므로 로그에 저장할 때 생략
            create_chat_log(db, user_id, user_message, chatbot_response)
            return chatbot_response