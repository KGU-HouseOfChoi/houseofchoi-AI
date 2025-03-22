# recommend_routes.py
import datetime
import random
import pymysql

from flask import Blueprint, jsonify
from db_utils import get_capstone_db_connection

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


@recommend_routes.route("/recommend_all/<int:user_id>", methods=["GET"])
def recommend_all_programs(user_id):
    """
    사용자 personality_tags와 elderly_programs 테이블의 tags를 비교해
    교집합(중복 태그)이 2개 이상인 모든 프로그램을 반환합니다.
    """
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

    # 5. 직렬화 가능하게 변환 후 결과 반환
    serializable_list = [make_json_serializable(item) for item in matched_list]
    return jsonify({
        "user_id": user_id,
        "matched_programs": serializable_list
    })

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
