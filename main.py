import pymysql
import random
import openai

from stt import speech_to_text
from tts import text_to_speech

##############################
# 1) 환경 설정
##############################

# DB 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "kkero0418",  # root 비밀번호
    "db": "elderly_db",
    "charset": "utf8mb4"
}

openai.api_key = "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"

# OpenAI 클라이언트 객체 생성
client = openai.OpenAI(api_key=openai.api_key)


def get_connection():
    return pymysql.connect(**DB_CONFIG)

##############################
# 2) GPT 호출 함수
##############################

def gpt_call(system_prompt, user_prompt, max_tokens=200):
    """
    최신 openai>=1.0.0 버전에서 호환되도록 GPT 호출 함수 수정
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # 또는 "gpt-4", "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] GPT 호출 실패: {e}")
        return user_prompt  # 실패 시 원본 텍스트 반환

##############################
# 3) DB 조회 & 추천 로직
##############################

def fetch_all_courses():
    """
    elderly_courses 테이블에서 모든 노인교실+강좌 데이터를 가져온다.
    예: [{'id':1, 'elderly_classroom_nm':'강북노인교실', 'course':'노래교실', ...}, ...]
    """
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = "SELECT * FROM elderly_courses"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
    finally:
        conn.close()

def get_course_personality(course_name):
    """
    course_personality 테이블에서 course_name의 성향(외향형/내향형/Unknown)을 가져온다.
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

def recommend_program(user_personality):
    """
    1) DB에서 모든 (노인교실+강좌) 조회
    2) user_personality와 일치하는 강좌만 필터링
    3) 무작위로 하나 골라 문자열 생성
    """
    courses = fetch_all_courses()
    if not courses:
        return None, "[ERROR] DB에 노인교실 데이터가 없습니다."

    matched_list = []
    for row in courses:
        c = row.get("course", "")
        ptype = get_course_personality(c)
        if ptype == user_personality:
            matched_list.append(row)

    if matched_list:
        chosen = random.choice(matched_list)
        # 기본 추천 문구
        raw_msg = (
            f"추천 프로그램입니다!\n"
            f"노인교실 이름: {chosen['elderly_classroom_nm']}\n"
            f"위치: {chosen['location']}\n"
            f"연락처: {chosen['tel_num']}\n"
            f"추천 강좌: {chosen['course']} ({user_personality})\n"
        )
        return chosen, raw_msg
    else:
        return None, f"'{user_personality}' 성향에 맞는 강좌를 찾지 못했습니다."

##############################
# 4) 메인 함수 (음성 챗봇)
##############################

def main():
    text_to_speech("안녕하세요, 음성 비서입니다. 외향형이신가요, 내향형이신가요? '그만'이라고 말씀하시면 종료합니다.")

    while True:
        user_input = speech_to_text()
        if not user_input:
            text_to_speech("음성을 인식하지 못했어요. 다시 말씀해주세요.")
            continue

        # '그만' 처리
        if "그만" in user_input:
            text_to_speech("대화를 종료합니다. 감사합니다.")
            return

        # 외향/내향 구분
        if "외향" in user_input:
            user_personality = "외향형"
        elif "내향" in user_input:
            user_personality = "내향형"
        else:
            text_to_speech("죄송해요, '외향' 또는 '내향' 중에서 말씀해주세요.")
            continue

        # DB 추천
        chosen, raw_msg = recommend_program(user_personality)

        # GPT로 메시지를 다듬기
        # (추천 메시지를 자연스러운 대화체로 개선)
        system_prompt = "당신은 친절한 한국어 음성 비서입니다. 다음 메시지를 사람에게 전달할 때, 자연스럽고 친근한 말투로 바꿔주세요."
        user_prompt = f"다음 문장을 자연스럽게 바꿔주세요:\n\n'{raw_msg}'\n\n반드시 60자 이내로 요약하지 말고, 자세히 말해주고 대화상대가 노인이라고 생각하고 최대한 부드럽고 말동무가 되는 느낌으로 말해줘."
        refined_msg = gpt_call(system_prompt, user_prompt, max_tokens=200)

        # 결과 출력
        print("[DEBUG] 원본 메시지:", raw_msg)
        print("[DEBUG] GPT 개선 메시지:", refined_msg)
        text_to_speech(refined_msg)

        # 추가 입력 루프 (필요 시)
        text_to_speech("더 궁금한 점이 있으면 말씀해 주세요. '그만'이라고 말하면 종료합니다.")
        follow_up = speech_to_text()
        if "그만" in follow_up:
            text_to_speech("대화를 종료합니다. 감사합니다.")
            return
        else:
            # 여기서 follow_up을 GPT에 넘기거나, 다시 user_personality를 묻는 등 확장 가능
            text_to_speech("알겠습니다. 다시 성향을 말씀해주세요. '그만'이라고 말하면 종료합니다.")


if __name__ == "__main__":
    main()
