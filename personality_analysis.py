import os
import re
import openai
import mysql.connector
from flask import Flask, request, jsonify
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
# ---------------------------
# [3] 설문 질문 데이터
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
    {"id": 10, "question": "스트레스 해소법?",               "choices": ["(A) 대화", "(B) 혼자 해결"]}
]

# ---------------------------
# [4] 질문 조회 API (JSON 반환)
# ---------------------------
@app.route('/', methods=['GET'])
def get_questions():
    """
    질문 목록을 JSON 형태로 반환합니다.
    """
    return jsonify(questions=QUESTIONS), 200

# ---------------------------
# [5] GPT 성향 분석 함수
# ---------------------------
def analyze_personality_gpt(prompt):
    """
    OpenAI API를 이용해 prompt에 대한 답변(분석 결과)을 반환.
    예외 발생 시, 오류 메시지를 문자열로 반환.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4 등을 사용할 수 있음
            messages=[
                {"role": "system", "content": "You are an AI assistant analyzing personality."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        gpt_result = response.choices[0].message.content.strip()
        return gpt_result if gpt_result else "분석 결과를 생성할 수 없습니다."
    except Exception as e:
        return f"OpenAI API 오류: {str(e)}"

# ---------------------------
# [6] 분석 엔드포인트 (A/B 답변 받기) - POST
# ---------------------------
@app.route('/analyze', methods=['POST'])
def analyze_personality():
    """
    사용자의 A/B 답변(10개)과 user_id를 입력받아
    GPT 분석 결과( E/I, S/N, T/F, J/P )를 DB에 저장한 뒤 JSON으로 반환합니다.
    """
    data = request.json
    user_answers = data.get("answers", [])
    user_id = data.get("user_id", None)

    if not user_answers or len(user_answers) != 10:
        return jsonify({"error": "답변 10개가 필요합니다."}), 400
    if user_id is None:
        return jsonify({"error": "user_id가 필요합니다."}), 400

    # 프롬프트 생성
    prompt = "사용자의 A/B 선택 결과를 바탕으로 성향을 분석하세요.\n"
    for i, answer in enumerate(user_answers, start=1):
        question_text = QUESTIONS[i-1]["question"]
        prompt += f"\nQ{i}. {question_text}\n사용자 선택: {answer}\n"

    prompt += """
아래 기준에 따라 사용자의 성향을 분석하고, 최종적으로 MBTI 요소를 출력하세요.

1. **외향적(E)인지 내향적(I)인지 판단하세요.**  
2. **감각형(S)인지 직관형(N)인지 판단하세요.**  
3. **사고형(T)인지 감정형(F)인지 판단하세요.**  
4. **판단형(J)인지 인식형(P)인지 판단하세요.**  

💡 **최종 결과는 아래 형식으로 출력하세요 (추가 설명 없이 MBTI 요소만 출력하세요):**  
E/I: (E 또는 I)  
S/N: (S 또는 N)  
T/F: (T 또는 F)  
J/P: (J 또는 P)
"""

    # GPT 분석 수행
    gpt_result = analyze_personality_gpt(prompt)

    # MBTI 요소 추출 (정규 표현식)
    match = re.search(
        r"E/I:\s*([EI])\s*\nS/N:\s*([SN])\s*\nT/F:\s*([TF])\s*\nJ/P:\s*([JP])", 
        gpt_result
    )
    if match:
        ei, sn, tf, jp = match.groups()
    else:
        return jsonify({"error": "GPT 분석 결과가 예상한 형식이 아닙니다.", "gpt_result": gpt_result}), 500

    # DB 저장
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
        INSERT INTO user_personality (user_id, ei, sn, tf, jp) 
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, ei, sn, tf, jp))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"DB 저장 오류: {str(e)}"}), 500

    # 결과 반환
    return jsonify({
        "user_id": user_id,
        "E/I": ei,
        "S/N": sn,
        "T/F": tf,
        "J/P": jp
    }), 200

# ---------------------------
# [7] 분석 결과 조회 (GET) - user_id로 조회
# ---------------------------
@app.route('/analysis/<int:user_id>', methods=['GET'])
def get_analysis(user_id):
    """
    특정 user_id의 MBTI 분석 결과를 조회 (챗봇 등에서 활용 가능).
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT user_id, ei, sn, tf, jp, created_at 
        FROM user_personality
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
        """
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"DB 조회 오류: {str(e)}"}), 500

    if not row:
        return jsonify({"error": f"user_id {user_id} 데이터가 없습니다."}), 404

    # 필요하다면, 하나의 필드로 합쳐서 반환할 수도 있음 (예: "ISTP")
    # mbti_str = f"{row['ei']}{row['sn']}{row['tf']}{row['jp']}"

    return jsonify({
        "user_id": row["user_id"],
        "E/I": row["ei"],
        "S/N": row["sn"],
        "T/F": row["tf"],
        "J/P": row["jp"],
        "created_at": str(row["created_at"])
        # "mbti": mbti_str
    }), 200

# ---------------------------
# [8] Flask 실행
# ---------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
