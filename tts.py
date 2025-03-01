import pyttsx3

def text_to_speech(text):
    """
    텍스트를 음성으로 출력(TTS)하는 함수
    """
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
