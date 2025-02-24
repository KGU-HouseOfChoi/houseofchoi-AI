import openai
import json
import xml.etree.ElementTree as ET
import speech_recognition as sr
import pyttsx3
import random
import base64
import os
from google.cloud import speech 
from google.oauth2 import service_account

##############################
# 사용자에게 필요한 설정
##############################

# 1) OpenAI API 키 설정 (실제 키로 교체)
openai.api_key = ""

# 2) Google Cloud Speech-to-Text JSON 파일 경로
GOOGLE_APPLICATION_CREDENTIALS = "stt.json"

# 서비스 계정 JSON을 이용하여 인증 객체 생성
credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS
)

# OpenAI 클라이언트 객체 (openai.api_key 설정으로 충분, 추가 호출 없어도 됨)
client = openai.OpenAI(api_key=openai.api_key)

def fetch_elderly_programs():
    print("[DEBUG] 노인 복지 프로그램 데이터를 로드합니다...")
    try:
        with open("elderly_programs.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict) or "DATA" not in data:
                raise ValueError(
                    "JSON 파일의 데이터 형식이 올바르지 않습니다. 'DATA' 키가 포함된 딕셔너리여야 합니다."
                )
            programs = data["DATA"]
            print(f"[DEBUG] 로드된 프로그램 개수: {len(programs)}")
            return programs
    except json.JSONDecodeError as e:
        print(f"JSON 디코딩 오류: {e}")
        return []
    except ValueError as ve:
        print(f"데이터 형식 오류: {ve}")
        return []
    except FileNotFoundError:
        print("[ERROR] 'elderly_programs.json' 파일을 찾을 수 없습니다.")
        return []

def speech_to_text():
    """
    Google Cloud Speech-to-Text API를 서비스 계정 JSON 파일로 인증하여 음성을 텍스트로 변환.
    (speech_recognition을 이용해 음성을 녹음하고, google.cloud.speech 라이브러리로 변환)
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("음성을 입력하세요... (5초 제한)")
        audio = recognizer.listen(source, phrase_time_limit=5)

    audio_data = audio.get_wav_data()

    client_speech = speech.SpeechClient(credentials=credentials)
    audio_bytes = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="ko-KR",
    )

    response = client_speech.recognize(config=config, audio=audio_bytes)
    if not response.results:
        print("음성을 인식하지 못했습니다. 다시 시도하세요.")
        return ""

    transcript = response.results[0].alternatives[0].transcript
    print(f"사용자 입력: {transcript}")
    return transcript

def text_to_speech(text):
    """ 텍스트를 음성으로 출력하는 함수 """
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def speak(text):
    """
    GPT API를 이용하여 자연스러운 응답 생성
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 친절한 음성 비서입니다. 사용자 요청을 돕는 역할을 합니다."},
                {"role": "user", "content": text}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"GPT 응답 오류: {e}")
        return text

def analyze_program_type(course):
    if not course:
        return "Unknown"
    print(f"[DEBUG] 분석할 강좌 정보: {course}")

    prompt = f"""
    다음은 노인 복지 프로그램의 한 강좌명입니다:
    \"{course}\"
    이 강좌가 외향적인 사람에게 적합한지, 내향적인 사람에게 적합한지 판단해주세요.
    출력은 '외향형' 또는 '내향형' 중 하나만 출력해주세요.
    """
    gpt_response = speak(prompt)
    print(f"[DEBUG] GPT 원본 응답: {gpt_response}")

    response_lower = gpt_response.lower()
    if "외향형" in response_lower:
        return "외향형"
    elif "내향형" in response_lower:
        return "내향형"
    else:
        return "Unknown"

def recommend_program(personality, programs):
    filtered_programs = []

    for program in programs:
        print(f"[DEBUG] 프로그램 데이터: {program}")
        if not isinstance(program, dict):
            print("잘못된 데이터 형식 감지: 프로그램 항목이 딕셔너리가 아닙니다.")
            continue

        course_list = program.get('course', '').split()
        categorized_courses = {"외향형": [], "내향형": []}

        for course in course_list:
            program_type = str(analyze_program_type(course)).strip()
            if program_type in ["외향형", "내향형"]:
                categorized_courses[program_type].append(course)
            else:
                print(f"[DEBUG] GPT 응답이 올바르지 않음: {program_type} (강좌: {course})")

        if len(categorized_courses[personality]) > 0:
            print(f"[DEBUG] 사용자의 성향({personality})과 일치하는 강좌 발견! -> {categorized_courses[personality]}")
            filtered_programs.append({
                **program,
                "matched_courses": categorized_courses[personality]
            })

    if filtered_programs:
        recommended = random.choice(filtered_programs)
        program_text = (
            f"당신의 성향({personality})에 맞춰 추천된 프로그램입니다.\n"
            f"📌 프로그램명: {recommended['elderly_classroom_nm']}\n"
            f"📍 위치: {recommended['location']}\n"
            f"📞 연락처: {recommended['tel_num']}\n"
            f"🎓 추천 강좌: {', '.join(recommended['matched_courses'])}"
        )
        print(f"[DEBUG] 최종 추천 프로그램: {program_text}")
        gpt_response = speak(program_text)
        return recommended, gpt_response

    print("[DEBUG] 필터링된 프로그램이 없습니다. 모든 프로그램을 다시 검색합니다.")
    random_program = random.choice(programs)
    return random_program, (
        f"사용자의 성향과 정확히 일치하는 강좌를 찾지 못했습니다. "
        f"대신 다음 프로그램을 추천합니다.\n"
        f"프로그램명: {random_program['elderly_classroom_nm']}\n"
        f"위치: {random_program['location']}\n"
        f"연락처: {random_program['tel_num']}\n"
        f"제공 강좌: {random_program['course']}"
    )

def main():
    programs = fetch_elderly_programs()
    if not programs:
        print("프로그램 데이터를 불러오지 못했습니다.")
        return

    text_to_speech("안녕하세요! 음성 비서입니다. 언제든 '그만'이라고 말씀하시면 대화를 종료합니다.")

    personality = None

    # [1] 외향/내향 질문
    while True:
        text_to_speech("당신은 외향형입니까, 내향형입니까?")
        user_input = speech_to_text()

        # '그만' 이라고 말하면 종료
        if "그만" in user_input:
            text_to_speech("대화를 종료합니다. 감사합니다.")
            return

        if "외향" in user_input:
            personality = "외향형"
            break
        elif "내향" in user_input:
            personality = "내향형"
            break
        else:
            text_to_speech("다시 입력해주세요. 외향, 내향 중에서 말씀해주세요.")

    # [2] 프로그램 추천
    text_to_speech(f"당신은 {personality} 성향입니다. 이에 맞는 프로그램을 추천해 드릴게요.")
    last_recommended, initial_gpt_response = recommend_program(personality, programs)
    if last_recommended is None:
        print(initial_gpt_response)
        text_to_speech(initial_gpt_response)
        return

    print(initial_gpt_response)
    text_to_speech(initial_gpt_response)

    # [3] 최종 요약 요청
    while True:
        text_to_speech("추가로 궁금하신 점이 있거나, 다른 질문이 있으시면 말씀해주세요. '그만'이라고 말씀하시면 종료합니다.")
        user_input = speech_to_text()

        if "그만" in user_input:
            text_to_speech("대화를 종료합니다. 감사합니다.")
            return

        # '프로그램 요약' 등 키워드 예시
        if "프로그램" in user_input and "요약" in user_input:
            final_prompt = """
            당신은 친절한 음성 비서입니다.
            위에서 추천한 프로그램에 대해 간단한 설명을 2~3줄로 작성해 주세요.
            반드시 "당신께는 어떤 프로그램을 추천드립니다"라는 문구를 포함하고,
            마지막에는 '감사합니다.' 라고 말해주세요.
            """
            final_summary = speak(final_prompt)
            print(final_summary)
            text_to_speech(final_summary)
        else:
            # 기타 사용자 요청 -> GPT에 직접 질의
            response = speak(user_input)
            print(response)
            text_to_speech(response)


if __name__ == "__main__":
    main()
