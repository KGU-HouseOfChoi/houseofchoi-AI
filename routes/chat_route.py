import random
from flask import Blueprint, request, jsonify
from db_utils import get_capstone_db_connection
from gpt_utils import gpt_call
from chat_utils import (
    recommend_random_program,
    search_program_and_build_message,
    extract_requested_program
)
from routes.schedule_route import save_schedule, save_conversation_log

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Body 예:
    {
      "user_id": "101",
      "message": "사용자 발화",
      "recommended_program": "노래교실"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    user_id = data.get("user_id", "").strip()
    user_message = data.get("message", "").strip()
    recommended_program = data.get("recommended_program")

    # (A) 사용자가 "예", "등록" 등으로 일정 등록 의사 표시
    if user_message.lower() in ["예", "네", "등록", "등록할래요"]:
        if recommended_program:
            success = save_schedule(user_id, recommended_program)
            if success:
                response_text = f"✅ '{recommended_program}' 일정이 등록되었습니다! (시간 미지정)"
                save_conversation_log(user_id, user_message, response_text)
                return jsonify({"user_id": user_id, "schedule": response_text})
            else:
                return jsonify({"error": "일정 등록 실패"}), 500
        else:
            return jsonify({"error": "추천된 프로그램명이 누락되었습니다.(recommended_program)"}), 400

    # (B) 사용자 메시지에서 프로그램명 추출
    requested_program = extract_requested_program(user_message)
    response = {"user_id": user_id}
    chatbot_response = ""

        # 🎯 (C-0) 대화 의도가 프로그램 추천과 무관할 경우 → 말벗 모드로 전환
    if requested_program is None:
        # 먼저 프로그램과 무관한 감성 대화인지 GPT에게 물어봄
        system_prompt = """
        다음 문장이 '복지 프로그램 추천을 요청하는 문장'인지 판단해 주세요.
        만약 추천 관련 요청이 아니고, 감성적인 말벗 대화나 일상적인 고민, 감정 표현이라면 '말벗'이라고만 답해주세요.
        예) '요즘 다리가 아파요' → 말벗
        예) '요가 수업 있어요?' → 추천
        """
        intent = gpt_call(system_prompt, user_message, max_tokens=10).strip().lower()

        if "말벗" in intent:
            # 감성적 말벗 응답 생성
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
            save_conversation_log(user_id, user_message, chatbot_response)
            return jsonify(response)

    # (C-1) 프로그램명이 언급되지 않았다면 => 무작위 추천
    if requested_program is None:
        raw_msg = recommend_random_program(user_id)
        system_prompt = "당신은 노인 복지 센터의 비서입니다. 아래 문장을 간단히 다듬어 주세요. 주어진 프로그램 정보를 바탕으로, 친근하고 간결하며 자연스러운 문장으로 추천 메시지를 작성해 주세요. 예시 형식은 아래와 같습니다:서예교실을 추천드릴께요. 창의적이고 감성적인 당신께 잘 어울릴꺼에요. 금요일 오후 2시부터 4시까지 SK청솔노인복지관에서 진행됩니다. 참가비는 한분기에 45,000원입니다. 등록하시겠습니까? 이제 아래 원시 데이터를 참고하여 같은 형식의 추천 메시지를 만들어 주세요."
        recommendation = gpt_call(system_prompt, raw_msg)
        response["recommendation"] = recommendation
        chatbot_response = recommendation
    else:
        # (C-2) 프로그램명이 언급되었다면 => DB 검색 or 안내 메시지
        raw_msg, found_program_name = search_program_and_build_message(requested_program)
        if found_program_name:
            system_prompt = "당신은 노인 복지 센터 비서입니다. 친절히 안내해 주세요.친근하고 간결하며 자연스러운 문장으로 추천 메시지를 작성해 주세요. 예시 형식은 아래와 같습니다:네 마침 SK청솔노인복지관에서 서예교실을 진행합니다다. 창의적이고 감성적인 당신께 잘 어울릴꺼에요. 금요일 오후 2시부터 4시까지 진행됩니다. 참가비는 한분기에에 45,000원입니다. 등록하시겠습니까? 이제 아래 원시 데이터를 참고하여 같은 형식의 추천 메시지를 만들어 주세요."
            recommendation = gpt_call(system_prompt, raw_msg)
            response["recommendation"] = recommendation
            chatbot_response = recommendation
            response["recommended_program"] = found_program_name
        else:
            system_prompt = "짧고 부드러운 말투로 안내해 주세요. 죄송하지만 저희가 연계하고 있는 센터에는 그 프로그램이 없습니다로시작해줘"
            assistant_answer = gpt_call(system_prompt, raw_msg)
            response["assistant_answer"] = assistant_answer
            chatbot_response = assistant_answer

    # (D) 대화 로그 저장
    save_conversation_log(user_id, user_message, chatbot_response)
    return jsonify(response)


@chat_bp.route("/chatlog/<user_id>", methods=["GET"])
def get_chat_log(user_id):
    """
    특정 user_id의 대화 기록 조회
    GET /chatlog/101
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT id, user_id, user_message, assistant_response, timestamp
                FROM user_conversation_log
                WHERE user_id = %s
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": f"대화 로그 조회 실패: {e}"}), 500
    finally:
        conn.close()
