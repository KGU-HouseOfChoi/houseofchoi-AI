import os
import openai
from dotenv import load_dotenv

load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

def gpt_call(system_prompt, user_prompt, max_tokens=200):
    """
    OpenAI 1.0.0 이상 버전에 맞춘 GPT 호출 함수
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
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
        return "죄송합니다. 다시 말씀해 주세요."