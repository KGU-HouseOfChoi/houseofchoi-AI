import speech_recognition as sr
from google.cloud import speech
from google.oauth2 import service_account

# 1) Google Cloud Speech-to-Text JSON 파일 경로
GOOGLE_APPLICATION_CREDENTIALS = "stt.json"

# 2) 서비스 계정 JSON을 이용하여 인증 객체 생성
credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS
)

def speech_to_text():
    """
    Google Cloud Speech-to-Text API를 이용하여 음성을 텍스트로 변환.
    (speech_recognition + google.cloud.speech)
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("음성을 입력하세요... (5초 제한)")
        audio = recognizer.listen(source, phrase_time_limit=5)

    audio_data = audio.get_wav_data()

    # Google Cloud Speech-to-Text 클라이언트
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
