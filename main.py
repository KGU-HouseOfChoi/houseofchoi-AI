from flask import Flask, request, jsonify
import pymysql
import random
import openai
import requests  # HTTP 요청

app = Flask(__name__)

##############################
# 1) DB 연결 설정
##############################

DB_CONFIG_ELDERLY = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "db": "elderly_db",  # 노인교실 DB (elderly_courses, user_conversation_log 등)
    "charset": "utf8mb4"
}

DB_CONFIG_PERSONALITY = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "db": "personality_db",  # 대화 로그, 성향 (user_conversation_log, user_personality 등)
    "charset": "utf8mb4"
}

# OpenAI API 키
openai.api_key = ""
client = openai.OpenAI(api_key=openai.api_key)

##############################
# 2) DB 연결 함수
##############################

def get_elderly_db_connection():
    """
    노인교실, 일정 관련 DB (elderly_db)
    """
    return pymysql.connect(**DB_CONFIG_ELDERLY)

def get_personality_db_connection():
    """
    사용자 대화 로그, 성향 관련 DB (personality_db)
    """
    return pymysql.connect(**DB_CONFIG_PERSONALITY)

##############################
# 2-1) 일정 등록 DB 함수
##############################

def save_schedule(user_id, program_name):
    """
    user_schedule 테이블에 일정 저장 (schedule_time=NULL)
    """
    conn = get_elderly_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user_schedule (user_id, program_name, schedule_time)
                VALUES (%s, %s, NULL)
            """
            cursor.execute(sql, (user_id, program_name))
            conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR] 일정 저장 실패: {e}")
        return False
    finally:
        conn.close()


##############################
# 2-3) 대화 로그 저장 함수
##############################

def save_conversation_log(user_id, user_message, assistant_response):
    """
    user_conversation_log 테이블에 대화 기록을 저장
    """
    conn = get_personality_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user_conversation_log (user_id, user_message, assistant_response)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_id, user_message, assistant_response))
            conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR] 대화 로그 저장 실패: {e}")
        return False
    finally:
        conn.close()

##############################
# 3) 사용자 성향 API
##############################

def fetch_user_personality(user_id):
    """
    외부 Flask 서버 API로 사용자 성향 정보 가져오기 (E/I 등)
    GET http://127.0.0.1:5000/analysis/<user_id>
    예: { "E/I": "I", "J/P": "J", ... }
    """
    api_url = f"http://127.0.0.1:5000/analysis/{user_id}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] API 요청 실패: {e}")
        return None

##############################
# 4) GPT 호출 함수
##############################

def gpt_call(system_prompt, user_prompt, max_tokens=200):
    """
    OpenAI 1.0.0 이상 버전에 맞춘 GPT 호출 함수
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] GPT 호출 실패: {e}")
        return "죄송합니다. 다시 말씀해 주세요."

##############################
# 5) 노인교실(강좌) 조회 & 추천 로직
##############################

def fetch_all_courses():
    """elderly_courses 테이블에서 모든 강좌 데이터를 가져옴"""
    conn = get_elderly_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM elderly_courses"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

def get_course_personality(course_name):
    """
    course_personality 테이블에서 해당 course_name의 성향(외향형/내향형) 조회
    """
    conn = get_elderly_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT personality_type
                FROM course_personality
                WHERE course_name = %s
                LIMIT 1
            """
            cursor.execute(sql, (course_name,))
            row = cursor.fetchone()
            return row[0] if row else None
    finally:
        conn.close()

def recommend_program(user_personality):
    """
    성향(E/I)에 맞는 프로그램 추천
    """
    courses = fetch_all_courses()
    if not courses:
        return None, "[ERROR] DB에 노인교실 데이터가 없습니다."

    matched_list = []
    for row in courses:
        course_name = row.get("course", "")
        ptype = get_course_personality(course_name)
        if ptype == user_personality:
            matched_list.append(row)

    if matched_list:
        chosen = random.choice(matched_list)
        raw_msg = (
            f"추천 프로그램입니다!\n"
            f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
            f"위치: {chosen['location']}\n"
            f"연락처: {chosen['tel_num']}\n"
            f"추천 강좌: {chosen['course']} ({user_personality})\n"
        )
        return chosen, raw_msg
    else:
        return None, f"'{user_personality}' 성향에 맞는 강좌를 찾지 못했습니다."


##############################
# 5-1) 프로그램 키워드 없이 => 무작위 추천
##############################

def recommend_random_program(user_id):
    """
    1) http://127.0.0.1:5000/analysis/<user_id> 에서 사용자 E/I 성향 가져옴
    2) E -> 외향형, I -> 내향형
    3) course_personality에서 personality_type이 해당 성향인 프로그램들 중 무작위 추천
    """

    # 1. 사용자 성향 가져오기
    personality_data = fetch_user_personality(user_id)
    if not personality_data:
        return "죄송합니다. 사용자 성향 정보를 가져오지 못했습니다."

    ei_value = personality_data.get("E/I")
    if ei_value == "E":
        target_personality = "외향형"
    elif ei_value == "I":
        target_personality = "내향형"
    else:
        return "죄송합니다. 알 수 없는 성향 정보입니다."

    # 2. 모든 강좌 가져오기
    courses = fetch_all_courses()
    if not courses:
        return "죄송합니다. 현재 등록된 프로그램이 없습니다."

    # 3. 사용자 성향에 맞는 강좌만 필터링
    matched_list = []
    for row in courses:
        course_name = row.get("course", "")
        ptype = get_course_personality(course_name)  # "외향형", "내향형", 등
        if ptype == target_personality:
            matched_list.append(row)

    if not matched_list:
        return f"'{target_personality}' 성향에 맞는 프로그램이 없습니다."

    # 4. 무작위로 1개 선택
    chosen = random.choice(matched_list)

    # 5. 안내 메시지 생성
    return (
        f"랜덤 추천 ({target_personality} 성향 기준)\n"
        f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
        f"위치: {chosen['location']}\n"
        f"연락처: {chosen['tel_num']}\n"
        f"추천 강좌: {chosen['course']}"
    )


##############################
# 추가 로직: 특정 프로그램 검색
##############################

def search_program_in_db(keyword):
    """
    DB에서 특정 키워드(예: "수영")가 포함된 프로그램을 검색
    """
    conn = get_elderly_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM elderly_courses WHERE course LIKE %s"
            cursor.execute(sql, (f"%{keyword}%",))
            return cursor.fetchall()
    finally:
        conn.close()

def generate_nonexistent_program_info(keyword):
    """
    GPT: 현재 센터에는 없지만, 사회적으로 존재하는 프로그램 안내
    """
    system_prompt = """
    당신은 노인 복지 센터에서 프로그램을 추천하는 비서입니다.
    사용자가 특정 프로그램(예: '수영')을 원하지만 DB에는 없을 때,
    '현재 센터에는 없지만, 일반적으로 이런 프로그램이 있을 수 있다'고 안내해 주세요.
    프로그램을 새로 창조하지 말고, 이미 사회에 흔히 존재하는 예시만 들어주세요.
    """
    user_prompt = f"지금 DB에는 '{keyword}' 관련 프로그램이 없어요. 하지만 일반적으로 이런 프로그램이 있을 수 있다고 설명해 주세요."
    return gpt_call(system_prompt, user_prompt)

def extract_requested_program(user_message):
    """
    GPT를 사용하여 사용자의 메시지에서 특정 프로그램을 원하는지 분석
    프로그램 명이 없다면 'None' 반환
    """
    system_prompt = """
    사용자 메시지에서 특정 프로그램명을 정확히 한 단어 또는 두 단어로 추출해 주세요.
    예를 들어, '요가 프로그램이 있나요?'라는 질문이 들어오면 '요가'만 반환해야 합니다.
    만약 프로그램명이 명확히 언급되지 않았다면 데이터형 'None'만 반환하세요.
    """
    candidate_program = gpt_call(system_prompt, user_message, max_tokens=20)

    if "None" in candidate_program.lower():
        return None
    return candidate_program.strip()

##############################
# 6) Flask API
##############################

@app.route("/")
def index():
    return "안녕하세요! 이 엔드포인트는 노인 복지 AI 챗봇 API 입니다."

@app.route("/chat", methods=["POST"])
def chat():
    """
    Body (JSON):
    {
      "user_id": "123",
      "message": "사용자 발화",
      "recommended_program": "노래교실" (일정 등록 시 함께 전달)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    user_id = data.get("user_id")
    user_message = data.get("message", "").strip()
    recommended_program = data.get("recommended_program", None)

    # (A) '예'라고 하면 일정 등록
    if user_message.lower() in ["예", "네", "등록", "등록할래요"]:
        if recommended_program:
            success = save_schedule(user_id, recommended_program)
            if success:
                response_text = f"✅ '{recommended_program}' 일정이 등록되었습니다! (현재 시간 미지정)"
                # 대화 로그 저장
                save_conversation_log(user_id, user_message, response_text)
                return jsonify({"user_id": user_id, "schedule": response_text})
            else:
                return jsonify({"error": "일정 등록 실패"}), 500
        else:
            return jsonify({"error": "추천된 프로그램명이 누락되었습니다.(recommended_program)"}), 400

    # [B] 특정 프로그램 요청 추출
    requested_program = extract_requested_program(user_message)

    recommendation = None
    assistant_answer = None

    if requested_program is None or requested_program.lower() == "none":
        # [C-1] 프로그램명이 None => 랜덤 프로그램 추천
        raw_msg = recommend_random_program(user_id)
        system_prompt = "당신은 친절한 한국어 음성 비서입니다. 당신의 성향에 맞는 프로그램을 무조건 추천합니다 하고 이 문장을 자연스럽게 바꿔주세요."
        recommendation = gpt_call(system_prompt, raw_msg)
    else:
        # [C-2] 프로그램명이 존재
        found_programs = search_program_in_db(requested_program)
        if found_programs:
            # DB에 있으면 => recommendation
            chosen = random.choice(found_programs)
            raw_msg = (
                f"[사용자가 '{requested_program}'를 요청]\n"
                f"프로그램이 DB에 있습니다!\n"
                f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
                f"위치: {chosen['location']}\n"
                f"연락처: {chosen['tel_num']}\n"
                f"강좌명: {chosen['course']}\n"
                f"일정 등록 원하시면 '예'라고 말하시고,\n"
                f"recommended_program: '{chosen['course']}' 로 보내주세요."
            )
            system_prompt = "당신은 친절한 한국어 음성 비서입니다. 찾아진 요소를 종합하여 하나의 문장으로 자연스럽게 만들고 친절한 말투로 다듬어 주세요."
            recommendation = gpt_call(system_prompt, raw_msg)
        else:
            # 없으면 => assistant_answer
            alt_info = generate_nonexistent_program_info(requested_program)
            raw_msg = (
                f"[사용자가 '{requested_program}'를 요청]\n"
                f"현재 센터에는 없지만, 이런 프로그램이 있을 수 있어요:\n{alt_info}"
            )
            system_prompt = "당신은 친절한 한국어 음성 비서입니다. 이 문장을 자연스럽게 다듬어주세요. 너무 길게 대답하진 말아주세요요"
            assistant_answer = gpt_call(system_prompt, raw_msg)

    # (C) 응답 구성
    response = {"user_id": user_id}

    chatbot_response = ""  # 실제 챗봇의 최종 답변 텍스트

    if recommendation:
        response["recommendation"] = recommendation
        chatbot_response = recommendation
    elif assistant_answer:
        response["assistant_answer"] = assistant_answer
        chatbot_response = assistant_answer

    # (D) 대화 로그 저장
    save_conversation_log(user_id, user_message, chatbot_response)

    return jsonify(response)

##############################
# 일정 조회 API 추가
##############################

@app.route("/schedule/<user_id>", methods=["GET"])
def get_user_schedule(user_id):
    """
    특정 user_id의 일정 목록을 조회하여 반환
    예: GET /schedule/123
    """
    conn = get_elderly_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT schedule_id, user_id, program_name, schedule_time, created_at
                FROM user_schedule
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        print(f"[ERROR] 일정 조회 실패: {e}")
        return jsonify({"error": "일정 조회 실패"}), 500
    finally:
        conn.close()

##############################
# 대화로그 API 추가
##############################
@app.route("/chatlog/<user_id>", methods=["GET"])
def get_chat_log(user_id):
    """
    특정 user_id의 대화 기록을 조회하여 반환
    예: GET /chatlog/123
    """
    conn = get_personality_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT id, user_id, user_message, assistant_response, timestamp
                FROM user_conversation_log
                WHERE user_id = %s
                ORDER BY timestamp DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        print(f"[ERROR] 대화 로그 조회 실패: {e}")
        return jsonify({"error": "대화 로그 조회 실패"}), 500
    finally:
        conn.close()

##############################
# 7) Flask 실행
##############################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
