import os
import mysql.connector
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

# ---------------------------
# [1] MySQL 설정
# ---------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_PERSONALITY_DB"),
    "charset": os.getenv("DB_CHARSET")
}

# ---------------------------
# [2] 13개 질문 데이터
# ---------------------------
QUESTIONS = [
    {"id": 1,  "question": "손주가 예고 없이 찾아오면?",         "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2,  "question": "새로운 기술을 배울 때?",           "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    {"id": 3,  "question": "혼자 VS 함께?",                 "choices": ["(A) 혼자가 좋다", "(B) 사람들과 함께"]},
    {"id": 4,  "question": "계획형 VS 즉흥형?",             "choices": ["(A) 미리 계획", "(B) 즉흥 결정"]},
    {"id": 5,  "question": "새로운 장소 vs 익숙한 장소?",      "choices": ["(A) 익숙한 곳", "(B) 새로운 곳"]},
    {"id": 6,  "question": "결정할 때?",                  "choices": ["(A) 신중하게", "(B) 직감으로"]},
    {"id": 7,  "question": "사회적 활동?",                 "choices": ["(A) 참여한다", "(B) 혼자가 좋다"]},
    {"id": 8,  "question": "변화를 좋아하는가?",             "choices": ["(A) 변화를 좋아함", "(B) 안정이 좋다"]},
    {"id": 9,  "question": "여가 시간?",                  "choices": ["(A) 새로운 도전", "(B) 익숙한 활동"]},
    {"id": 10, "question": "스트레스 해소법?",               "choices": ["(A) 대화", "(B) 혼자 해결"]},

    # 온보딩 3문항
    {"id": 11, "question": "운동을 선호하시나요?",         "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 12, "question": "혼자 활동을 좋아하시나요?",    "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 13, "question": "조용한 활동을 선호하시나요?",  "choices": ["(A) 예", "(B) 아니요"]},
]

# ---------------------------
# [3] MBTI 분석 함수 (앞 10개)
# ---------------------------
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

# ---------------------------
# [4] MBTI -> 태그
# ---------------------------
def analyze_mbti_tags(mbti_str):
    tags = []
    if 'E' in mbti_str:
        tags.append("외향적")
        tags.append("사회적")
    else:
        tags.append("내향적")
        tags.append("정적인")

    if 'S' in mbti_str:
        tags.append("현실적")
        tags.append("체험형")
    else:
        tags.append("창의적")
        tags.append("예술적")

    if 'T' in mbti_str:
        tags.append("분석적")
        tags.append("논리적")
    else:
        tags.append("감성적")
        tags.append("교류형")

    if 'J' in mbti_str:
        tags.append("구조적")
        tags.append("조직적")
    else:
        tags.append("자유로운")
        tags.append("유동적")
    return tags

# ---------------------------
# [5] 온보딩 3문항 -> 태그
# ---------------------------
def analyze_onboarding_tags(answers_3):
    tags = []
    # answers_3[0] -> 운동_선호
    if answers_3[0] == 'A':  # 예
        tags.append("활동적")
    else:                    # 아니요
        tags.append("정적인")

    # answers_3[1] -> 혼자_활동
    if answers_3[1] == 'A':  # 예
        tags.append("내향적")
    else:                    # 아니요
        tags.append("외향적")

    # answers_3[2] -> 조용한_활동
    if answers_3[2] == 'A':  # 예
        tags.append("정적인")
    else:
        tags.append("활동적")

    return tags

# ---------------------------
# [6] 13문항 종합 처리
# ---------------------------
def analyze_13_answers(answers_13):
    if len(answers_13) != 13:
        raise ValueError("정확히 13개의 답변이 필요합니다.")
    
    # (1) 1~10 -> MBTI
    ei, sn, tf, jp = analyze_mbti_from_10(answers_13[:10])
    mbti_str = f"{ei}{sn}{tf}{jp}"

    # (2) MBTI 태그
    mbti_tags = analyze_mbti_tags(mbti_str)

    # (3) 11~13 -> 온보딩 태그
    onboard_tags = analyze_onboarding_tags(answers_13[10:])

    # (4) 합치고 중복 제거
    all_tags = list(set(mbti_tags + onboard_tags))
    return mbti_str, all_tags

# ---------------------------
# [7] 질문 목록 조회 (GET)
# ---------------------------
@app.route('/', methods=['GET'])
def get_questions():
    return jsonify(questions=QUESTIONS), 200

# ---------------------------
# [8] 성향 분석 + DB 저장 (POST)
# ---------------------------
@app.route('/analyze', methods=['POST'])
def analyze_personality():
    """
    JSON 예시:
    {
      "user_id": 123,
      "answers": ["A","B","A","B","A","B","A","B","A","B","A","B","A"]  # 13개
    }
    """
    data = request.json
    user_id = data.get("user_id")
    answers_13 = data.get("answers", [])

    if user_id is None:
        return jsonify({"error": "user_id가 필요합니다."}), 400
    if len(answers_13) != 13:
        return jsonify({"error": "A/B 답변 13개가 필요합니다."}), 400

    # 분석
    try:
        mbti_str, all_tags = analyze_13_answers(answers_13)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # DB 저장
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        tags_str = ",".join(all_tags)  # DB에 쉼표로 구분 저장

        # user_personality 테이블에 personality_tags 컬럼이 있다고 가정
        query = """
        INSERT INTO user_personality (user_id, ei, sn, tf, jp, personality_tags)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        ei, sn, tf, jp = mbti_str[0], mbti_str[1], mbti_str[2], mbti_str[3]
        cursor.execute(query, (user_id, ei, sn, tf, jp, tags_str))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as ex:
        return jsonify({"error": f"DB 저장 오류: {str(ex)}"}), 500

    # 결과 응답
    return jsonify({
        "user_id": user_id,
        "mbti": mbti_str,
        "personality_tags": all_tags
    }), 200

# ---------------------------
# [9] 분석 결과 조회 (GET)
# ---------------------------
@app.route('/analysis/<int:user_id>', methods=['GET'])
def get_analysis(user_id):
    """
    user_id의 가장 최근 분석 결과 조회
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT user_id, ei, sn, tf, jp, personality_tags, created_at
            FROM user_personality
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as ex:
        return jsonify({"error": f"DB 조회 오류: {str(ex)}"}), 500

    if not row:
        return jsonify({"error": f"user_id {user_id} 데이터가 없습니다."}), 404

    # MBTI 문자열 생성
    mbti_str = f"{row['ei']}{row['sn']}{row['tf']}{row['jp']}"

    # 태그를 리스트로 변환 (비어있으면 빈 리스트)
    tags_list = row["personality_tags"].split(',') if row["personality_tags"] else []

    return jsonify({
        "user_id": row["user_id"],
        "ei": row["ei"],  # E/I
        "sn": row["sn"],  # S/N
        "tf": row["tf"],  # T/F
        "jp": row["jp"],  # J/P
        "mbti": mbti_str,  # MBTI (예: "ENTP")
        "personality_tags": tags_list,  # 태그 목록 (배열)
        "created_at": str(row["created_at"])  # 생성 시간
    }), 200

# ---------------------------
# [10] 서버 실행
# ---------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
