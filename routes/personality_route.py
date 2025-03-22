import json
import pymysql
from flask import Blueprint, request, jsonify
from db_utils import get_capstone_db_connection  # DB 연결 함수 (예: capstone DB)
from gpt_utils import gpt_call

personality_bp = Blueprint("personality_bp", __name__)

# 1) 13문항 질문 (온보딩)
QUESTIONS = [
    {"id": 1,  "question": "손주가 예고 없이 찾아오면?",    "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2,  "question": "새로운 기술을 배울 때?",       "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    {"id": 3,  "question": "혼자 VS 함께?",             "choices": ["(A) 혼자가 좋다", "(B) 사람들과 함께"]},
    {"id": 4,  "question": "계획형 VS 즉흥형?",         "choices": ["(A) 미리 계획", "(B) 즉흥 결정"]},
    {"id": 5,  "question": "새로운 장소 vs 익숙한 장소?",  "choices": ["(A) 익숙한 곳", "(B) 새로운 곳"]},
    {"id": 6,  "question": "결정할 때?",              "choices": ["(A) 신중하게", "(B) 직감으로"]},
    {"id": 7,  "question": "사회적 활동?",             "choices": ["(A) 참여한다", "(B) 혼자가 좋다"]},
    {"id": 8,  "question": "변화를 좋아하는가?",         "choices": ["(A) 변화를 좋아함", "(B) 안정이 좋다"]},
    {"id": 9,  "question": "여가 시간?",              "choices": ["(A) 새로운 도전", "(B) 익숙한 활동"]},
    {"id": 10, "question": "스트레스 해소법?",           "choices": ["(A) 대화", "(B) 혼자 해결"]},
    {"id": 11, "question": "운동을 선호하시나요?",      "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 12, "question": "혼자 활동을 좋아하시나요?", "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 13, "question": "조용한 활동을 선호하시나요?", "choices": ["(A) 예", "(B) 아니요"]},
]

@personality_bp.route("/questions", methods=["GET"])
def get_questions():
    return jsonify({"questions": QUESTIONS}), 200


@personality_bp.route("/analyze", methods=["POST"])
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

    conn = get_capstone_db_connection()
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


@personality_bp.route("/analysis/<int:user_id>", methods=["GET"])
def get_analysis(user_id):
    conn = get_capstone_db_connection()
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


@personality_bp.route("/analyze/<user_id>", methods=["POST"])
def analyze_user_conversation(user_id):
    """
    POST /analyze/<user_id>?days=30
    최근 N일(기본 30일)간의 대화 로그를 기반으로, 사용자의 성향 변화(각 축: ei, sn, tf, jp)를 분석하여
    변화가 감지되면 DB의 해당 필드와 태그(personality_tags)를 업데이트합니다.
    
    GPT에게 아래와 같이 JSON 형식으로 응답하도록 요청합니다:
    {
      "ei": "NEW_E" 또는 "NEW_I" 또는 "NO_CHANGE",
      "sn": "NEW_S" 또는 "NEW_N" 또는 "NO_CHANGE",
      "tf": "NEW_T" 또는 "NEW_F" 또는 "NO_CHANGE",
      "jp": "NEW_J" 또는 "NEW_P" 또는 "NO_CHANGE"
    }
    """
    days = request.args.get("days", 30)
    conn = get_capstone_db_connection()
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
                "당신은 노인 복지센터 AI 분석가입니다. 최근 대화를 바탕으로 사용자의 성향 변화 여부를 분석하세요. "
                "아래 JSON 형식으로 결과를 출력하세요. 각 항목은 변경된 경우 새 값을, 변화가 없으면 'NO_CHANGE'로 출력하세요.\n"
                "{\n"
                '  "ei": "NEW_E" 또는 "NEW_I" 또는 "NO_CHANGE",\n'
                '  "sn": "NEW_S" 또는 "NEW_N" 또는 "NO_CHANGE",\n'
                '  "tf": "NEW_T" 또는 "NEW_F" 또는 "NO_CHANGE",\n'
                '  "jp": "NEW_J" 또는 "NEW_P" 또는 "NO_CHANGE"\n'
                "}\n"
                "예를 들어, 만약 대화에서 내향적 성향이 강화되면 {\"ei\": \"NEW_I\", \"sn\": \"NO_CHANGE\", \"tf\": \"NO_CHANGE\", \"jp\": \"NO_CHANGE\"}와 같이 응답하세요."
            )
            user_prompt = f"최근 {days}일간 사용자 대화:\n{conversation_text}"
            
            gpt_result = gpt_call(system_prompt, user_prompt)
            print("[DEBUG] GPT 분석 결과:", gpt_result)
            
            try:
                changes = json.loads(gpt_result)
            except Exception as e:
                return jsonify({"error": "GPT 결과 JSON 파싱 실패"}), 500
            
            # 현재 DB에 저장된 성향 조회
            sql_current = """
                SELECT ei, sn, tf, jp
                FROM user_personality
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql_current, (user_id,))
            current_row = cursor.fetchone()
            if not current_row:
                return jsonify({"error": f"{user_id} 사용자의 기존 성향 데이터가 없습니다."}), 404
            
            # 각 성향 업데이트 결정 (NEW_ 접두사가 있으면 새 값, NO_CHANGE면 현재 값 유지)
            def get_updated(current, change):
                if change.startswith("NEW_"):
                    return change[-1]  # 마지막 문자(E, I, S, N, T, F, J, P)
                return current
            
            updated_ei = get_updated(current_row["ei"], changes.get("ei", "NO_CHANGE"))
            updated_sn = get_updated(current_row["sn"], changes.get("sn", "NO_CHANGE"))
            updated_tf = get_updated(current_row["tf"], changes.get("tf", "NO_CHANGE"))
            updated_jp = get_updated(current_row["jp"], changes.get("jp", "NO_CHANGE"))
            
            # 만약 아무 것도 변경되지 않았다면
            if (updated_ei == current_row["ei"] and updated_sn == current_row["sn"] and
                updated_tf == current_row["tf"] and updated_jp == current_row["jp"]):
                return jsonify({"message": "성향 변화 없음"}), 200
            
            # 새 MBTI 문자열 생성
            new_mbti = f"{updated_ei}{updated_sn}{updated_tf}{updated_jp}"
            # 업데이트된 태그 재계산 (analyze_mbti_tags 함수 사용; 해당 함수는 아래에 정의됨)
            new_tags = analyze_mbti_tags(new_mbti)
            tags_str = ",".join(new_tags)
            
            sql_update = """
                UPDATE user_personality
                SET ei=%s, sn=%s, tf=%s, jp=%s, personality_tags=%s
                WHERE user_id=%s
                ORDER BY id DESC
                LIMIT 1
            """
            cursor.execute(sql_update, (updated_ei, updated_sn, updated_tf, updated_jp, tags_str, user_id))
            conn.commit()
            
            return jsonify({
                "message": f"성향 업데이트 완료. 새 MBTI: {new_mbti}, 태그: {tags_str}"
            }), 200
            
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        return jsonify({"error": "분석 중 오류 발생"}), 500
    finally:
        conn.close()


# ---------------------------
# 아래는 MBTI/온보딩 분석 로직 함수들
# ---------------------------
def analyze_13_answers(answers_13):
    if len(answers_13) != 13:
        raise ValueError("정확히 13개의 A/B 답변이 필요합니다.")
    ei, sn, tf, jp = analyze_mbti_from_10(answers_13[:10])
    mbti_str = f"{ei}{sn}{tf}{jp}"
    mbti_tags = analyze_mbti_tags(mbti_str)
    onboard_tags = analyze_onboarding_tags(answers_13[10:])
    all_tags = list(set(mbti_tags + onboard_tags))
    return mbti_str, all_tags

def analyze_mbti_from_10(answers_10):
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
    score = {'E':0, 'I':0, 'S':0, 'N':0, 'T':0, 'F':0, 'J':0, 'P':0}
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
    if answers_3[0] == 'A':
        tags.append("활동적")
    else:
        tags.append("정적인")
    if answers_3[1] == 'A':
        tags.append("내향적")
    else:
        tags.append("외향적")
    if answers_3[2] == 'A':
        tags.append("정적인")
    else:
        tags.append("활동적")
    return tags
