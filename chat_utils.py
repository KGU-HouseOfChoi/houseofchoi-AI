import random
import requests
import pymysql

from db_utils import get_elderly_db_connection
from gpt_utils import gpt_call

def fetch_user_personality(user_id):
    """
    외부 Flask API: http://127.0.0.1:5000/analysis/<user_id>
    """
    api_url = f"http://127.0.0.1:5000/analysis/{user_id}"
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] 사용자 성향 fetch 실패: {e}")
        return None

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
    1) 사용자 성향 정보 => ei 필드 (E->외향형, I->내향형)
    2) course_personality에서 matching
    3) 강좌 중 무작위
    """
    personality_data = fetch_user_personality(user_id)
    if not personality_data:
        return "죄송합니다. 사용자 성향 정보를 가져오지 못했습니다."

    ei_value = personality_data.get("ei", "")
    if ei_value == "E":
        target_personality = "외향형"
    elif ei_value == "I":
        target_personality = "내향형"
    else:
        return "죄송합니다. 알 수 없는 성향 정보입니다."

    courses = fetch_all_courses()
    if not courses:
        return "죄송합니다. 현재 등록된 프로그램이 없습니다."

    matched_list = []
    for row in courses:
        ptype = get_course_personality(row["course"])
        if ptype == target_personality:
            matched_list.append(row)

    if not matched_list:
        return f"'{target_personality}' 성향에 맞는 프로그램이 없습니다."

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
