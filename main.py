import os
import random
import pymysql
import openai

import requests  # HTTP 요청
from dotenv import load_dotenv
from flask import Flask, request, jsonify

##############################
# 0) .env 파일 로드 & 설정
##############################
load_dotenv()

app = Flask(__name__)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

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
# DB 설정
##############################
DB_CONFIG_ELDERLY = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_ELDERLY_DB"),
    "charset": os.getenv("DB_CHARSET")
}

DB_CONFIG_PERSONALITY = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_PERSONALITY_DB"),
    "charset": os.getenv("DB_CHARSET")
}

def get_elderly_db_connection():
    """노인교실, 일정 관련 DB (elderly_db)"""
    return pymysql.connect(**DB_CONFIG_ELDERLY)

def get_personality_db_connection():
    """사용자 대화 로그, 성향 관련 DB (personality_db)"""
    return pymysql.connect(**DB_CONFIG_PERSONALITY)

##############################
# 1) 메인 페이지
##############################
@app.route("/")
def index():
    return "안녕하세요! 노인 복지 AI 챗봇 API (개선 버전) 입니다."

##############################
# 2) 일정 등록 / 대화 로그
##############################
def save_schedule(user_id, program_name):
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
        print(f"[ERROR] 일정 등록 실패: {e}")
        return False
    finally:
        conn.close()

def save_conversation_log(user_id, user_message, assistant_response):
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
# 3) 사용자 성향 가져오기 (외부 Flask API)
##############################
def fetch_user_personality(user_id):
    # 이 API 주소는 실제로 127.0.0.1:5000/analysis/<user_id> 에서 가져온다는 가정
    api_url = f"http://127.0.0.1:5000/analysis/{user_id}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] 사용자 성향 fetch 실패: {e}")
        return None
    
# --------------------------------------------------------
# (2) 일정 저장 / 대화 로그 저장
# --------------------------------------------------------
def save_schedule(user_id, program_name):
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

def save_conversation_log(user_id, user_message, assistant_response):
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

# --------------------------------------------------------
# (3) 노인교실(강좌) 조회 & 추천 로직 (유지)
# --------------------------------------------------------
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
    course_personality 테이블에서 해당 course_name의 성향(외향형/내향형 등) 조회
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

# ---------------------------
# 4) 노인교실(강좌) 조회 & 추천 로직
# ---------------------------
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
    course_personality 테이블에서 해당 course_name의 성향(외향형/내향형 등) 조회
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

def recommend_random_program(user_id):
    """
    1) 사용자 성향 정보 => ei 필드 사용
       E => "외향형", I => "내향형"
    2) course_personality 에서 personality_type="외향형"/"내향형"
    3) 해당 강좌 중 무작위 추천
    """
    # 1. 사용자 성향 정보 가져오기
    personality_data = fetch_user_personality(user_id)
    if not personality_data:
        return "죄송합니다. 사용자 성향 정보를 가져오지 못했습니다."

    # 2. ei => 외향형 / 내향형
    ei_value = personality_data.get("ei", "")
    if ei_value == "E":
        target_personality = "외향형"
    elif ei_value == "I":
        target_personality = "내향형"
    else:
        return "죄송합니다. 알 수 없는 성향 정보입니다."

    # 3. 모든 강좌 조회
    courses = fetch_all_courses()
    if not courses:
        return "죄송합니다. 현재 등록된 프로그램이 없습니다."

    # 4. 사용자 성향에 맞는 강좌만 필터링
    matched_list = []
    for row in courses:
        course_name = row.get("course", "")
        ptype = get_course_personality(course_name)  # "외향형" or "내향형"
        if ptype == target_personality:
            matched_list.append(row)

    if not matched_list:
        return f"'{target_personality}' 성향에 맞는 프로그램이 없습니다."

    # 5. 무작위 하나 추천
    chosen = random.choice(matched_list)
    return (
        f"랜덤 추천 ({target_personality} 성향 기준)\n"
        f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
        f"위치: {chosen['location']}\n"
        f"연락처: {chosen['tel_num']}\n"
        f"추천 강좌: {chosen['course']}"
    )

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
    user_prompt = (
        f"지금 DB에는 '{keyword}' 관련 프로그램이 없어요. "
        f"하지만 일반적으로 이런 프로그램이 있을 수 있다고 설명해 주세요."
    )
    return gpt_call(system_prompt, user_prompt)

def extract_requested_program(user_message):
    """
    GPT를 사용하여 사용자의 메시지에서 특정 프로그램명을 추출.
    예) "요가 프로그램이 있나요?" -> "요가"
    프로그램명이 없으면 None 반환
    """
    system_prompt = """
    사용자 메시지에서 특정 프로그램명을 정확히 한 단어 또는 두 단어로 추출해 주세요.
    예를 들어, '요가 프로그램이 있나요?'라는 질문이 들어오면 '요가'만 반환해야 합니다.
    만약 프로그램명이 명확히 언급되지 않았다면 데이터형 'None'만 반환하세요.
    """
    candidate_program = gpt_call(system_prompt, user_message, max_tokens=20)

    if "none" in candidate_program.lower():
        return None
    return candidate_program.strip()

# ------------------------------------------------
# [Chat API]
# ------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    """
    예:
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

    # (A) '예'로 답하면 => 일정 등록
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

    # (B) 메시지에서 프로그램명 추출
    requested_program = extract_requested_program(user_message)

    response = {"user_id": user_id}
    chatbot_response = ""

    if requested_program is None or requested_program.lower() == "none":
        # (C-1) 프로그램 없음 => 무작위 추천
        raw_msg = recommend_random_program(user_id)
        system_prompt = (
            "당신은 노인 복지 센터의 비서입니다.\n"
            "아래 안내 문장을 간단하고 친절하게 다듬어 주세요."
        )
        recommendation = gpt_call(system_prompt, raw_msg)
        response["recommendation"] = recommendation
        chatbot_response = recommendation
    else:
        # (C-2) DB 검색
        found_programs = search_program_in_db(requested_program)
        if found_programs:
            chosen = random.choice(found_programs)
            raw_msg = (
                f"[사용자가 '{requested_program}' 요청]\n"
                f"프로그램이 DB에 있습니다!\n"
                f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
                f"위치: {chosen['location']}\n"
                f"연락처: {chosen['tel_num']}\n"
                f"강좌명: {chosen['course']}\n"
                f"일정을 등록하시려면 '예'라고 답해주세요.\n"
                f"(recommended_program: '{chosen['course']}')"
            )
            system_prompt = (
                "당신은 노인 복지 센터의 비서입니다.\n"
                "위 정보를 간결히 합쳐서, 하나의 문장으로 안내해 주세요."
            )
            recommendation = gpt_call(system_prompt, raw_msg)
            response["recommendation"] = recommendation
            chatbot_response = recommendation
        else:
            # DB에 없으면 => nonexistent_program_info
            alt_info = generate_nonexistent_program_info(requested_program)
            raw_msg = (
                f"[사용자가 '{requested_program}' 요청]\n"
                f"현재 센터에는 없지만, 이런 프로그램이 있을 수 있습니다:\n{alt_info}"
            )
            system_prompt = (
                "당신은 노인 복지 센터의 비서입니다.\n"
                "짧고 친절한 말투로 안내해 주세요."
            )
            assistant_answer = gpt_call(system_prompt, raw_msg)
            response["assistant_answer"] = assistant_answer
            chatbot_response = assistant_answer

    # (D) 대화 로그 저장
    save_conversation_log(user_id, user_message, chatbot_response)
    return jsonify(response)

##############################
# 7) 일정 조회 API
##############################
@app.route("/schedule/<user_id>", methods=["GET"])
def get_user_schedule(user_id):
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
            rows = cursor.fetchall()
            return jsonify(rows), 200
    except Exception as e:
        print(f"[ERROR] 일정 조회 실패: {e}")
        return jsonify({"error": "일정 조회 실패"}), 500
    finally:
        conn.close()

##############################
# 8) 대화 로그 조회 API
##############################
@app.route("/chatlog/<user_id>", methods=["GET"])
def get_chat_log(user_id):
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
            rows = cursor.fetchall()
            return jsonify(rows), 200
    except Exception as e:
        print(f"[ERROR] 대화 로그 조회 실패: {e}")
        return jsonify({"error": "대화 로그 조회 실패"}), 500
    finally:
        conn.close()

##############################
# 9) EI 성향 기반 전체 프로그램 반환
##############################
@app.route("/recommend_all/<user_id>", methods=["GET"])
def recommend_all_programs(user_id):
    personality_data = fetch_user_personality(user_id)
    if not personality_data:
        return jsonify({"error": "사용자 성향 정보를 가져오지 못했습니다."}), 404

    ei_value = personality_data.get("ei", "")
    if ei_value == "E":
        target_personality = "외향형"
    elif ei_value == "I":
        target_personality = "내향형"
    else:
        return jsonify({"error": "알 수 없는 성향 정보입니다."}), 400

    courses = fetch_all_courses()
    if not courses:
        return jsonify({"error": "현재 등록된 프로그램이 없습니다."}), 404

    matched_list = []
    for row in courses:
        if get_course_personality(row["course"]) == target_personality:
            matched_list.append(row)

    if not matched_list:
        return jsonify({"message": f"'{target_personality}' 성향에 맞는 프로그램이 없습니다."}), 404

    return jsonify({
        "user_id": user_id,
        "성향": target_personality,
        "matched_programs": matched_list
    })

################################################################
# [모듈 2] 13문항 성향(온보딩) API (예시)
################################################################
QUESTIONS = [
    {"id": 1, "question": "손주가 예고 없이 찾아오면?", "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2, "question": "새로운 기술을 배울 때?", "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    # ...
    {"id": 13, "question": "조용한 활동을 선호하시나요?", "choices": ["(A) 예", "(B) 아니요"]},
]

@app.route("/questions", methods=["GET"])
def get_questions():
    return jsonify({"questions": QUESTIONS}), 200

def analyze_mbti_from_10(answers_10):
    # 예시 로직
    question_map = {
        1: ('EI', {'A': 'E', 'B': 'I'}),
        2: ('SN', {'A': 'S', 'B': 'N'}),
        3: ('EI', {'A': 'I', 'B': 'E'}),
        4: ('JP', {'A': 'J', 'B': 'P'}),
        5: ('SN', {'A': 'S', 'B': 'N'}),
        6: ('TF', {'A': 'T', 'B': 'F'}),
        7: ('EI', {'A': 'E', 'B': 'I'}),
        8: ('TF', {'A': 'F', 'B': 'T'}),
        9: ('SN', {'A': 'N', 'B': 'S'}),
        10: ('JP', {'A': 'P', 'B': 'J'})
    }
    score = dict(E=0,I=0,S=0,N=0,T=0,F=0,J=0,P=0)
    for i, ans in enumerate(answers_10, start=1):
        dim, ab_map = question_map[i]
        if ans in ab_map:
            score[ab_map[ans]] += 1
    ei = 'E' if score['E'] >= score['I'] else 'I'
    sn = 'S' if score['S'] >= score['N'] else 'N'
    tf = 'T' if score['T'] >= score['F'] else 'F'
    jp = 'J' if score['J'] >= score['P'] else 'P'
    return ei, sn, tf, jp

def analyze_mbti_tags(mbti_str):
    tags = []
    if 'E' in mbti_str:
        tags += ["외향적", "사회적"]
    else:
        tags += ["내향적", "정적인"]

    if 'S' in mbti_str:
        tags += ["현실적", "체험형"]
    else:
        tags += ["창의적", "예술적"]

    if 'T' in mbti_str:
        tags += ["분석적", "논리적"]
    else:
        tags += ["감성적", "교류형"]

    if 'J' in mbti_str:
        tags += ["구조적", "조직적"]
    else:
        tags += ["자유로운", "유동적"]

    return tags

def analyze_onboarding_tags(answers_3):
    tags = []
    # 11번 (운동 선호)
    if answers_3[0] == 'A':
        tags.append("활동적")
    else:
        tags.append("정적인")

    # 12번 (혼자 활동)
    if answers_3[1] == 'A':
        tags.append("내향적")
    else:
        tags.append("외향적")

    # 13번 (조용한 활동)
    if answers_3[2] == 'A':
        tags.append("정적인")
    else:
        tags.append("활동적")

    return tags

def analyze_13_answers(answers_13):
    if len(answers_13) != 13:
        raise ValueError("정확히 13개의 A/B 답변이 필요합니다.")
    ei, sn, tf, jp = analyze_mbti_from_10(answers_13[:10])
    mbti_str = f"{ei}{sn}{tf}{jp}"

    mbti_tags = analyze_mbti_tags(mbti_str)
    onboard_tags = analyze_onboarding_tags(answers_13[10:])

    all_tags = list(set(mbti_tags + onboard_tags))
    return mbti_str, all_tags

@app.route("/analyze", methods=["POST"])
def analyze_personality():
    data = request.json
    user_id = data.get("user_id")
    answers_13 = data.get("answers", [])

    if not user_id:
        return jsonify({"error": "user_id가 필요합니다."}), 400
    if len(answers_13) != 13:
        return jsonify({"error": "정확히 13개의 A/B 답변이 필요합니다."}), 400

    try:
        mbti_str, all_tags = analyze_13_answers(answers_13)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    conn = get_personality_db_connection()
    try:
        with conn.cursor() as cursor:
            tags_str = ",".join(all_tags)
            sql = """
            INSERT INTO user_personality (user_id, ei, sn, tf, jp, personality_tags)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            ei, sn, tf, jp = mbti_str[0], mbti_str[1], mbti_str[2], mbti_str[3]
            cursor.execute(sql, (user_id, ei, sn, tf, jp, tags_str))
            conn.commit()
    except Exception as ex:
        return jsonify({"error": f"DB 저장 오류: {str(ex)}"}), 500
    finally:
        conn.close()

    return jsonify({
        "user_id": user_id,
        "mbti": mbti_str,
        "personality_tags": all_tags
    }), 200

@app.route("/analysis/<int:user_id>", methods=["GET"])
def get_analysis(user_id):
    conn = get_personality_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT user_id, ei, sn, tf, jp, personality_tags, created_at
                FROM user_personality
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
    except Exception as ex:
        return jsonify({"error": f"DB 조회 오류: {str(ex)}"}), 500
    finally:
        conn.close()

    if not row:
        return jsonify({"error": f"user_id {user_id} 데이터가 없습니다."}), 404

    mbti_str = f"{row['ei']}{row['sn']}{row['tf']}{row['jp']}"
    tags_list = row["personality_tags"].split(',') if row["personality_tags"] else []

    return jsonify({
        "user_id": row["user_id"],
        "ei": row["ei"],
        "sn": row["sn"],
        "tf": row["tf"],
        "jp": row["jp"],
        "mbti": mbti_str,
        "personality_tags": tags_list,
        "created_at": str(row["created_at"])
    }), 200

##############################
# [모듈 3] 대화 로그 분석 -> EI 변경
##############################
@app.route("/analyze/<user_id>", methods=["POST"])
def analyze_user_conversation(user_id):
    days = request.args.get("days", 30)
    conn = get_personality_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql_logs = """
                SELECT user_message
                FROM user_conversation_log
                WHERE user_id = %s
                  AND timestamp >= NOW() - INTERVAL %s DAY
                ORDER BY timestamp DESC
            """
            cursor.execute(sql_logs, (user_id, days))
            logs = cursor.fetchall()
            if not logs:
                return jsonify({"message": f"{days}일간 대화 기록이 없어 분석 불가"}), 400

            conversation_text = "\n".join([row["user_message"] for row in logs])
            system_prompt = (
                "당신은 노인 복지센터 AI 분석가입니다.\n"
                "최근 대화를 보고, 사용자의 외향/내향 변화를 감지해 주세요.\n"
                "1) 외향(E)로 바뀌면 'NEW_E', 2) 내향(I)로 바뀌면 'NEW_I', "
                "3) 변화 없거나 불확실하면 'NO_CHANGE'라고만 답하세요."
            )
            user_prompt = f"최근 {days}일간 사용자 대화:\n{conversation_text}"

            gpt_result = gpt_call(system_prompt, user_prompt)
            print("[DEBUG] GPT 분석 결과:", gpt_result)

            sql_current = """
                SELECT ei
                FROM user_personality
                WHERE user_id=%s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql_current, (user_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": f"{user_id} 사용자의 기존 성향 데이터가 없습니다."}), 404

            current_ei = row["ei"]
            if gpt_result == "NEW_E" and current_ei != "E":
                sql_update = """
                    UPDATE user_personality
                    SET ei='E'
                    WHERE user_id=%s
                    ORDER BY id DESC
                    LIMIT 1
                """
                cursor.execute(sql_update, (user_id,))
                conn.commit()
                return jsonify({"message": "성향이 외향형(E)으로 업데이트되었습니다."}), 200
            elif gpt_result == "NEW_I" and current_ei != "I":
                sql_update = """
                    UPDATE user_personality
                    SET ei='I'
                    WHERE user_id=%s
                    ORDER BY id DESC
                    LIMIT 1
                """
                cursor.execute(sql_update, (user_id,))
                conn.commit()
                return jsonify({"message": "성향이 내향형(I)으로 업데이트되었습니다."}), 200
            elif gpt_result == "NO_CHANGE":
                return jsonify({"message": "성향 변화 없음"}), 200
            else:
                return jsonify({"message": "성향 변화 없음 또는 이미 동일 성향"}), 200
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        return jsonify({"error": "분석 중 오류 발생"}), 500
    finally:
        conn.close()

##############################
# 메인 실행
##############################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
