import datetime
import random
import pymysql

from flask import Blueprint, jsonify, request
from db_utils import get_capstone_db_connection
from .schedule_route import save_schedule

recommend_routes = Blueprint('recommend_routes', __name__)


def fetch_user_personality(user_id):
    """
    DB에서 user_personality 테이블의 최신 성향 데이터를 가져옵니다.
    예시 반환:
    {
      "user_id": 101,
      "ei": "E",
      "sn": "N",
      "tf": "T",
      "jp": "P",
      "personality_tags": "외향적,사회적,활동적"
    }
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT user_id, ei, sn, tf, jp, personality_tags
                FROM user_personality
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return row
    except Exception as e:
        print(f"[ERROR] 사용자 성향 fetch 실패: {e}")
        return None
    finally:
        conn.close()


def fetch_all_courses():
    """
    elderly_programs 테이블에서 모든 강좌 데이터를 가져옵니다.
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM elderly_programs"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def get_course_personality(course_name):
    """
    course_personality 테이블에서 해당 course_name의 성향(예: '외향형', '내향형')을 조회합니다.
    """
    conn = get_capstone_db_connection()
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


def make_json_serializable(row):
    """
    딕셔너리 row의 값 중 datetime이나 timedelta 객체가 있으면 문자열로 변환.
    Flask jsonify로 반환하기 전에 필요한 처리를 합니다.
    """
    for key, value in row.items():
        if isinstance(value, (datetime.datetime, datetime.timedelta)):
            row[key] = str(value)
    return row



@recommend_routes.route("/recommend_all/<int:user_id>", methods=["GET", "POST"])
def recommend_all_programs(user_id):
    """
    GET 요청 시:
      - 사용자 personality_tags와 elderly_programs 테이블의 tags를 비교하여
        교집합(중복 태그)이 2개 이상인 모든 프로그램을 반환합니다.
    
    POST 요청 시:
      - 클라이언트에서 전송된 JSON 데이터를 기반으로 추천된 프로그램을 일정으로 등록합니다.
      - 요청 본문의 user_id와 URL의 user_id가 일치해야 합니다.
    """
    if request.method == "GET":
        # 1. 사용자 성향(태그) 가져오기
        conn = get_capstone_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT personality_tags
                    FROM user_personality
                    WHERE user_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                """
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
                if not row or not row.get("personality_tags"):
                    return jsonify({"error": "사용자 성향 정보를 가져오지 못했습니다."}), 404
                user_tags_str = row["personality_tags"]
                user_tags = [tag.strip() for tag in user_tags_str.split(",") if tag.strip()]
        finally:
            conn.close()

        # 2. 모든 프로그램 정보 가져오기 (elderly_programs 테이블)
        conn = get_capstone_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM elderly_programs"
                cursor.execute(sql)
                courses = cursor.fetchall()
        finally:
            conn.close()

        if not courses:
            return jsonify({"error": "현재 등록된 프로그램이 없습니다."}), 404

        # 3. 각 프로그램의 tags와 사용자 태그 비교 (교집합 개수가 2개 이상이면 추천 목록에 추가)
        matched_list = []
        for course in courses:
            course_tags_str = course.get("tags", "")
            course_tags = [tag.strip() for tag in course_tags_str.split(",") if tag.strip()]
            overlap = set(user_tags) & set(course_tags)
            if len(overlap) >= 2:
                matched_list.append(course)

        # 4. 매칭 결과가 없으면 404, 있으면 리스트 반환
        if not matched_list:
            return jsonify({"message": "사용자 성향에 맞는 프로그램이 없습니다."}), 404

        serializable_list = [make_json_serializable(item) for item in matched_list]
        return jsonify({
            "user_id": user_id,
            "matched_programs": serializable_list
        })

    elif request.method == "POST":
        # POST: 추천 프로그램을 일정으로 추가하는 기능
        data = request.get_json()
        json_user_id = data.get("user_id")
        program_name = data.get("program_name")
        요일1 = data.get("요일1")
        요일2 = data.get("요일2")
        요일3 = data.get("요일3")
        요일4 = data.get("요일4")
        요일5 = data.get("요일5")
        시작시간 = data.get("시작시간")
        종료시간 = data.get("종료시간")
        
        # 필수 항목 체크 및 URL과 본문 user_id 일치 확인
        if not all([json_user_id, program_name, 시작시간, 종료시간]):
            return jsonify({"error": "필수 항목이 누락되었습니다."}), 400
        if int(json_user_id) != user_id:
            return jsonify({"error": "URL의 user_id와 요청 본문의 user_id가 일치하지 않습니다."}), 400

        success = save_schedule(user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간)
        if success:
            return jsonify({"message": "일정이 저장되었습니다."}), 200
        else:
            return jsonify({"error": "일정 저장에 실패하였습니다."}), 500

def recommend_random_program(user_id):
    """
    사용자의 personality_tags와 elderly_programs 테이블의 tags를 비교해
    교집합(중복 태그)이 2개 이상인 프로그램 중 하나를 무작위로 추천합니다.
    """
    # 1. 사용자 태그 가져오기
    conn = get_capstone_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT personality_tags
                FROM user_personality
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            if not row or not row.get("personality_tags"):
                return "죄송합니다. 사용자 성향 정보를 가져오지 못했습니다."

            user_tags_str = row["personality_tags"]
            user_tags = [tag.strip() for tag in user_tags_str.split(",") if tag.strip()]
    finally:
        conn.close()

    # 2. 모든 프로그램 정보 가져오기
    conn = get_capstone_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM elderly_programs"
            cursor.execute(sql)
            courses = cursor.fetchall()
    finally:
        conn.close()

    if not courses:
        return "죄송합니다. 현재 등록된 프로그램이 없습니다."

    # 3. 사용자 태그와 비교하여 교집합이 2개 이상이면 추천 후보에 추가
    matched_list = []
    for course in courses:
        course_tags_str = course.get("tags", "")
        course_tags = [tag.strip() for tag in course_tags_str.split(",") if tag.strip()]
        overlap = set(user_tags) & set(course_tags)
        if len(overlap) >= 2:
            matched_list.append(course)

    if not matched_list:
        return "사용자 성향에 맞는 프로그램이 없습니다."

    # 4. 무작위 추천
    chosen = random.choice(matched_list)
    message = (
    f"✅ 추천 프로그램이 있습니다!\n\n"
    f"📌 프로그램명: {chosen.get('프로그램명', '')}\n"
    f"🏢 기관명: {chosen.get('기관명', '')}\n"
    f"📍 주소: {chosen.get('주소', '')}\n"
    f"📞 연락처: {chosen.get('tel', '')}\n"
    f"🕒 시간: {chosen.get('시작시간', '')} ~ {chosen.get('종료시간', '')}\n"
    f"💰 금액: {chosen.get('금액', '')}\n"
    f"🧾 카테고리: {chosen.get('main_category', '')} / {chosen.get('sub_category', '')}\n"
    f"👥 정원: {chosen.get('headcount', '')}\n"
    f"🏷️ 태그: {chosen.get('tags', '')}"
)
    return message
