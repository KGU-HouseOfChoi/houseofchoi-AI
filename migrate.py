import csv
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
    "db": os.getenv("DB_NAME", "capstone"),  # 기본값 capstone
    "charset": os.getenv("DB_CHARSET", "utf8mb4")
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

##############################
# 3) GPT 호출 함수
##############################
def gpt_call(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 노인 복지 프로그램을 분석하는 AI입니다."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] GPT 호출 실패: {e}")
        return "Unknown"

##############################
# 4) CSV → DB 저장
##############################
def load_programs_from_csv(csv_file_path):
    rows = []
    # DictReader로 전체 읽기
    with open(csv_file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def insert_program_to_db(row):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO elderly_programs
                (프로그램명, 요일1, 요일2, 요일3, 요일4, 요일5,
                 시작시간, 종료시간, 금액, 기관명, 위도, 경도, 주소, tel,
                 main_category, sub_category, headcount, tags)
                VALUES
                (%s, %s, %s, %s, %s, %s,
                 %s, %s, %s, %s, %s, %s, %s, %s,
                 '교양', '실내', '개인', '')
            """
            cursor.execute(sql, (
                row.get("프로그램명", ""),
                row.get("요일1", ""),
                row.get("요일2", ""),
                row.get("요일3", ""),
                row.get("요일4", ""),
                row.get("요일5", ""),
                row.get("시작시간", None),
                row.get("종료시간", None),
                row.get("금액", ""),
                row.get("기관명", ""),
                row.get("위도", None),
                row.get("경도", None),
                row.get("주소", ""),
                row.get("tel", "")
            ))
            conn.commit()
    finally:
        conn.close()

##############################
# 5) GPT 분석 후 DB 업데이트
##############################
def analyze_program_category(program_name):
    prompt = f"""
    강좌명: '{program_name}'
    이 강좌를 다음과 같이 분류해 주세요:
    1) 대분류(main_category): 운동, 음악, 예술, 디지털, 어학, 문해, 교양 중에서만 하나
    2) 중분류1(sub_category): 실내, 실외 중에서만 하나
    3) 중분류2(headcount): 개인, 단체 중에서만 하나나
    4) 소분류(tags): '외향적', '사회적', '내향적', '정적인', '현실적', '체험형', '창의적', '예술적', '분석적', '논리적', '감성적', '교류형', '구조적', '조직적', '자유로운', '유동적', '활동적' 중에서만 최대 5개 키워드를 쉼표로 구분

    아래 JSON 형태로만 출력하세요:
    {{
        "main_category": "...",
        "sub_category": "...",
        "headcount": "...",
        "tags": ["...", "..."]
    }}
    """
    result = gpt_call(prompt)
    try:
        data = json.loads(result)
        main_cat = data.get("main_category", "교양")
        sub_cat = data.get("sub_category", "실내")
        head = data.get("headcount", "개인")
        tags_list = data.get("tags", [])
        tags_str = ",".join(tags_list)

        # DB UPDATE
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE elderly_programs
                    SET main_category=%s,
                        sub_category=%s,
                        headcount=%s,
                        tags=%s
                    WHERE 프로그램명=%s
                """
                cursor.execute(sql, (main_cat, sub_cat, head, tags_str, program_name))
                conn.commit()
        finally:
            conn.close()

        print(f"[INFO] '{program_name}' → main:{main_cat}, sub:{sub_cat}, head:{head}, tags:{tags_str}")
    except Exception as e:
        print(f"[ERROR] JSON 파싱 실패: {e}")

##############################
# 6) 메인 실행 (디버그 코드 추가)
##############################
def migrate_csv_to_db(csv_file_path):
    # 0) CSV 첫 줄 디버깅
    with open(csv_file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        first_row = next(reader, None)
        print("[DEBUG] CSV 첫 줄:", first_row)

    # 1) CSV 로드
    programs = load_programs_from_csv(csv_file_path)
    if not programs:
        print("[ERROR] CSV 데이터가 없습니다.")
        return

    # 2) DB 삽입
    for row in programs:
        insert_program_to_db(row)

    # 3) GPT로 각 프로그램 분류 후 UPDATE
    program_names = set([p["프로그램명"] for p in programs if p.get("프로그램명")])
    for pname in program_names:
        analyze_program_category(pname)

if __name__ == "__main__":
    csv_path = "data/elderly_program.CSV"
    migrate_csv_to_db(csv_path)
