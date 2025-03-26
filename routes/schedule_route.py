from flask import Blueprint, jsonify
import pymysql
import datetime
from utils.db_utils import get_capstone_db_connection

schedule_bp = Blueprint("schedule_bp", __name__)

def save_schedule(user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간):
    """
    user_schedule 테이블에 일정 정보를 저장합니다.
    새로운 DB 스키마에서는 요일1~요일5, 시작시간, 종료시간 컬럼을 사용하며,
    프로그램 이름은 'program_name' 컬럼에 저장합니다.
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user_schedule 
                  (user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간))
            conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR] 일정 저장 실패: {e}")
        return False
    finally:
        conn.close()


def save_conversation_log(user_id, user_message, assistant_response, recommended_program=None):
    """
    user_conversation_log 테이블에 대화 로그를 저장합니다.
    추천된 프로그램이 있으면 recommended_program 컬럼에 함께 저장합니다.
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user_conversation_log (user_id, user_message, assistant_response, recommended_program)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, user_message, assistant_response, recommended_program))
            conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR] 대화 로그 저장 실패: {e}")
        return False
    finally:
        conn.close()


def save_conversation_log(user_id, user_message, assistant_response, recommended_program=None):
    """
    user_conversation_log 테이블에 대화 로그를 저장합니다.
    추천된 프로그램이 있으면 recommended_program 컬럼에 함께 저장합니다.
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO user_conversation_log (user_id, user_message, assistant_response, recommended_program)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, user_message, assistant_response, recommended_program))
            conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR] 대화 로그 저장 실패: {e}")
        return False
    finally:
        conn.close()


def make_json_serializable(row):
    for key, value in row.items():
        if isinstance(value, (datetime.datetime, datetime.date, datetime.timedelta)):
            row[key] = str(value)
    return row

@schedule_bp.route("/schedule/<user_id>", methods=["GET"])
def get_user_schedule(user_id):
    """
    GET /schedule/101
    일정 목록을 조회합니다. (program_name, 요일1~요일5, 시작시간, 종료시간 등)
    """
    conn = get_capstone_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT schedule_id, user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간, created_at
                FROM user_schedule
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            rows = [make_json_serializable(row) for row in rows]
            return jsonify(rows), 200
    except Exception as e:
        print(f"[ERROR] 일정 조회 실패: {e}")
        return jsonify({"error": "일정 조회 실패"}), 500
    finally:
        conn.close()