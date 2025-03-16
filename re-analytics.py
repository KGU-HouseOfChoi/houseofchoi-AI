from flask import Flask, request, jsonify
import pymysql
import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

# ---------------------------
# [1] OpenAI 설정
# ---------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

# ---------------------------
# [2] MySQL 설정
# ---------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_PERSONALITY_DB"),
    "charset": os.getenv("DB_CHARSET")
}
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

##############################
# 2) GPT 호출 함수 (새로운 방식)
##############################
def gpt_call(system_prompt, user_prompt, max_tokens=200):
    """
    GPT에게 메시지를 보내고 응답을 받는 함수 (1.0.0+ 인터페이스)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-3.5-turbo 등
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
        return "분석 오류"

##############################
# 3) 사용자 대화 분석 -> 성향 업데이트
##############################
@app.route("/analyze/<user_id>", methods=["POST"])
def analyze_user_conversation(user_id):
    days = request.args.get("days", 30)
    conn = get_db_connection()
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

            system_prompt = """
            당신은 노인 복지센터 AI 분석가입니다.
            사용자 대화를 읽고 외향(E) ↔ 내향(I) 성향 변화를 감지하세요.
            """
            user_prompt = f"""
최근 {days}일간의 사용자 대화 내용:
{conversation_text}

위 대화 내용을 종합해 볼 때,
1) 사용자 성향이 'E'(외향)로 바뀌었다면 "NEW_E"라고만 답하고,
2) 'I'(내향)로 바뀌었다면 "NEW_I"라고만 답해주세요.
3) 변화가 없거나 아직 불확실하다면 "NO_CHANGE"라고만 답하세요.
            """

            gpt_result = gpt_call(system_prompt, user_prompt, max_tokens=100)
            print("[DEBUG] GPT 분석 결과:", gpt_result)

            # user_personality 테이블에서 현재 성향
            sql_current = "SELECT ei FROM user_personality WHERE user_id=%s LIMIT 1"
            cursor.execute(sql_current, (user_id,))
            row = cursor.fetchone()
            current_ei = row["ei"] if row else None

            if not current_ei:
                return jsonify({"error": f"{user_id} 사용자의 기존 성향 데이터가 없습니다."}), 404

            # GPT 결과 해석
            if gpt_result == "NEW_E" and current_ei != "E":
                sql_update = "UPDATE user_personality SET ei='E' WHERE user_id=%s"
                cursor.execute(sql_update, (user_id,))
                conn.commit()
                return jsonify({"message": "성향이 외향형(E)으로 업데이트되었습니다."}), 200
            elif gpt_result == "NEW_I" and current_ei != "I":
                sql_update = "UPDATE user_personality SET ei='I' WHERE user_id=%s"
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
