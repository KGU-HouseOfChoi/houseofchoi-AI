import json
import pymysql
import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

##############################
# 1) OpenAI 설정
##############################
openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=openai.api_key)

##############################
# 2) MySQL 설정
##############################
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_ELDERLY_DB"),
    "charset": os.getenv("DB_CHARSET")
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)

##############################
# 3) GPT 호출 함수
##############################
def gpt_call(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # 또는 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "당신은 노인 복지 프로그램을 분석하는 AI입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        # ChatCompletion 결과에서 텍스트만 추출
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] GPT 호출 실패: {e}")
        return "Unknown"

##############################
# 4) 코스(강좌) 성향 분석 & 캐싱
##############################
def get_course_personality(course_name):
    """
    course_personality 테이블에서 이미 분석된 코스인지 확인
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT personality_type FROM course_personality WHERE course_name=%s LIMIT 1"
            cursor.execute(sql, (course_name,))
            row = cursor.fetchone()
            return row[0] if row else None
    finally:
        conn.close()

def insert_course_personality(course_name, personality_type):
    """
    course_personality 테이블에 (course_name, personality_type) 저장
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO course_personality (course_name, personality_type)
                VALUES (%s, %s)
            """
            cursor.execute(sql, (course_name, personality_type))
            conn.commit()
    finally:
        conn.close()

def analyze_course_personality(course_name):
    """
    1) DB에서 코스 성향이 있는지 확인
    2) 없으면 GPT로 분석
    3) '외향형', '내향형', 'Unknown' 중 하나를 DB에 저장
    4) 결과 반환
    """
    cached = get_course_personality(course_name)
    if cached:
        print(f"[INFO] 이미 분석된 강좌: {course_name} → {cached}")
        return cached

    prompt = f"""
    강좌명: '{course_name}'
    이 강좌가 외향적인 사람에게 적합한지, 내향적인 사람에게 적합한지 판단해 주세요.
    '외향형' 혹은 '내향형' 중 하나로만 답변 바랍니다.
    """
    result = gpt_call(prompt).lower()

    if "외향형" in result:
        ptype = "외향형"
    elif "내향형" in result:
        ptype = "내향형"
    else:
        ptype = "Unknown"

    insert_course_personality(course_name, ptype)
    return ptype

##############################
# 5) JSON → DB (elderly_courses)
##############################
def load_programs_from_json():
    """
    elderly_programs.json에서 모든 노인교실 정보를 로드
    구조 예시: {"DATA":[{"elderly_classroom_nm":"...", "location":"...", "course":"노래교실 요가", "tel_num":"...", "no":1}, ...]}
    """
    with open("elderly_programs.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("DATA", [])

def migrate_json_to_db():
    """
    JSON 데이터를 읽어, 강좌(코스)를 개별 행으로 나눈 뒤,
    DB 테이블 `elderly_courses` 에 삽입 + GPT 분석 결과를 `course_personality`에 저장
    """
    print("[INFO] 노인 복지 프로그램 데이터를 JSON에서 가져옵니다...")
    programs = load_programs_from_json()
    if not programs:
        print("[ERROR] JSON 파일이 비거나 DATA가 없습니다.")
        return

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for item in programs:
                nm = item.get("elderly_classroom_nm", "").strip()
                loc = item.get("location", "").strip()
                course_str = item.get("course", "").strip()
                tel = item.get("tel_num", "").strip()
                no_ = item.get("no", 0)

                # 공백으로 구분된 강좌를 각각 별도 행으로 저장
                course_list = course_str.split()
                for c in course_list:
                    # 1) DB에 삽입
                    sql_insert = """
                        INSERT INTO elderly_courses
                        (elderly_classroom_nm, location, course, tel_num, no)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert, (nm, loc, c, tel, no_))

                    # 2) 외향/내향 분석 후 course_personality에 저장
                    analyze_course_personality(c)

            conn.commit()
            print("[INFO] 모든 노인교실 데이터를 강좌별 개별 행으로 DB에 저장했습니다.")

    finally:
        conn.close()

##############################
# 6) 실행
##############################
if __name__ == "__main__":
    migrate_json_to_db()
