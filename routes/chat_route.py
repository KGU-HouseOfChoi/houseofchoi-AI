import random
from flask import Blueprint, request, jsonify

from db_utils import get_personality_db_connection
from gpt_utils import gpt_call
from chat_utils import (
    recommend_random_program,
    search_program_in_db,
    generate_nonexistent_program_info,
    extract_requested_program
)
# schedule_route.py의 save_schedule, save_conversation_log 함수 임포트
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

    # (A) "예" => 일정 등록
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

    # (B) 프로그램 추출
    requested_program = extract_requested_program(user_message)
    response = {"user_id": user_id}
    chatbot_response = ""

    if requested_program is None:
        # (C-1) => 무작위 추천
        raw_msg = recommend_random_program(user_id)
        system_prompt = "당신은 노인 복지 센터의 비서입니다. 아래 문장을 간단히 다듬어 주세요."
        recommendation = gpt_call(system_prompt, raw_msg)
        response["recommendation"] = recommendation
        chatbot_response = recommendation
    else:
        # (C-2) DB 검색
        found = search_program_in_db(requested_program)
        if found:
            chosen = random.choice(found)
            raw_msg = (
                f"[사용자가 '{requested_program}' 요청]\n"
                f"프로그램이 DB에 있습니다!\n"
                f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
                f"위치: {chosen['location']}\n"
                f"연락처: {chosen['tel_num']}\n"
                f"강좌명: {chosen['course']}\n"
                f"일정을 등록하시려면 '예'라고 말씀하세요.\n"
                f"(recommended_program: '{chosen['course']}')"
            )
            system_prompt = "당신은 노인 복지 센터 비서입니다. 친절히 안내해 주세요."
            recommendation = gpt_call(system_prompt, raw_msg)
            response["recommendation"] = recommendation
            chatbot_response = recommendation
        else:
            # DB에 없으면
            alt_info = generate_nonexistent_program_info(requested_program)
            raw_msg = (
                f"[사용자가 '{requested_program}' 요청]\n"
                f"현재 센터에는 없지만, 이런 프로그램이 있을 수 있어요:\n{alt_info}"
            )
            system_prompt = "짧고 부드러운 말투로 안내해 주세요."
            assistant_answer = gpt_call(system_prompt, raw_msg)
            response["assistant_answer"] = assistant_answer
            chatbot_response = assistant_answer

    # (D) 대화 로그
    save_conversation_log(user_id, user_message, chatbot_response)
    return jsonify(response)


@chat_bp.route("/chatlog/<user_id>", methods=["GET"])
def get_chat_log(user_id):
    """
    특정 user_id의 대화 기록 조회
    GET /chatlog/101
    """
    conn = get_personality_db_connection()
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
        return jsonify({"error": "대화 로그 조회 실패"}), 500
    finally:
        conn.close()
