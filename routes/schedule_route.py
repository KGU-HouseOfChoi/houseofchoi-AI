from flask import Blueprint, jsonify
from db_utils import get_elderly_db_connection, get_personality_db_connection
import pymysql

schedule_bp = Blueprint("schedule_bp", __name__)

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

@schedule_bp.route("/schedule/<user_id>", methods=["GET"])
def get_user_schedule(user_id):
    """
    GET /schedule/101
    일정 목록 조회
    """
    conn = get_elderly_db_connection()
    try:
        with conn.cursor() as cursor:
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
        return jsonify({"error": "일정 조회 실패"}), 500
    finally:
        conn.close()
