---

```markdown
# 🤖 노인복지 GPT 챗봇 API

GPT 기반의 **맞춤형 노인복지 프로그램 추천 챗봇 API**입니다.  
사용자의 성향을 분석하고, 복지 프로그램 추천부터 일정 등록, 감성적 대화까지 지원합니다.

---

## 🚀 핵심 기능

| 기능 | 설명 |
|------|------|
| 온보딩 질문 | MBTI 및 활동 성향 기반 사용자 성향 추출 |
| 프로그램 추천 | 성향 기반 복지 프로그램 추천 |
| 감성 대화 | 일반 대화 시 따뜻한 말벗 역할 수행 |
| 일정 등록 | 추천 프로그램을 사용자 일정에 저장 |
| 대화 기록 | 모든 발화를 저장하고 분석 가능 |

---

## ⚙️ 실행 방법

### ✅ 1. 가상환경(venv) 실행

```bash
# 환경 변수 파일 설정
cp .env.example .env

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

### ✅ 2. Docker 환경 실행

```bash
docker-compose up -d
```

---

## 📚 API 문서

### 📌 GET `/questions`  
**온보딩 질문 목록 조회**

```json
{
  "questions": [
    {
      "id": 1,
      "question": "손주가 예고 없이 찾아오면?",
      "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]
    }
  ]
}
```

---

### 📌 POST `/analyze`  
**온보딩 답변 분석 및 저장**

```json
{
  "user_id": "101",
  "answers": ["A", "B", ..., "A"]
}
```

```json
{
  "user_id": "101",
  "mbti": "ENFP",
  "personality_tags": ["외향적", "사회적", "활동적"]
}
```

---

### 📌 GET `/recommend_all/<user_id>`  
**성향 기반 프로그램 전체 추천**

```json
{
  "user_id": 101,
  "matched_programs": [
    {
      "프로그램명": "서예교실",
      "기관명": "SK노인복지관",
      "tags": "감성적, 창의적, 정적인"
    }
  ]
}
```

---

### 📌 POST `/chat`  
**GPT 챗봇 대화 요청**

**요청**

```json
{
  "user_id": "101",
  "message": "요가 프로그램 있나요?"
}
```

**응답 - 추천 존재 시**

```json
{
  "user_id": "101",
  "recommendation": "네, SK복지관에서 요가 수업이 진행 중이에요. 등록하시겠어요?",
  "recommended_program": "요가"
}
```

**응답 - 감성 대화 시**

```json
{
  "user_id": "101",
  "assistant_answer": "요즘 많이 힘드셨겠어요. 제가 곁에 있어드릴게요."
}
```

---

### 📌 일정 등록 (내부 처리)  
**조건**: `"예"`, `"등록"` 등의 의사 표현 시 자동 등록

```json
{
  "user_id": "101",
  "schedule": "✅ '서예교실' 일정이 등록되었습니다!"
}
```

---

### 📌 GET `/schedule/<user_id>`  
**사용자 일정 조회**

```json
[
  {
    "program_name": "서예교실",
    "요일1": "화",
    "요일3": "목",
    "시작시간": "10:00",
    "종료시간": "12:00"
  }
]
```

---

### 📌 GET `/analysis/<user_id>`  
**성향 분석 결과 조회**

```json
{
  "user_id": 101,
  "mbti": "ENFP",
  "personality_tags": ["외향적", "창의적", "감성적"],
  "created_at": "2025-03-22 10:12:00"
}
```

---

### 📌 POST `/analyze/<user_id>?days=30`  
**최근 대화 기반 성향 재분석**

```json
{
  "message": "성향 업데이트 완료. 새 MBTI: ISFJ, 태그: 내향적, 현실적, 감성적, 구조적"
}
```

---

### 📌 GET `/chatlog/<user_id>`  
**사용자 대화 기록 조회**

```json
[
  {
    "user_id": 101,
    "user_message": "요즘 너무 외로워요",
    "assistant_response": "제가 항상 곁에 있어요. 언제든지 말 걸어주세요.",
    "timestamp": "2025-03-22T10:13:45"
  }
]
```

---

## 📂 환경 변수 (.env)

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=capstone
DB_CHARSET=utf8mb4

OPENAI_API_KEY=sk-...
```

---

## 🧱 데이터베이스 테이블 요약

| 테이블명 | 설명 |
|----------|------|
| `user_personality` | MBTI 및 태그 기반 사용자 성향 정보 |
| `elderly_programs` | 복지 프로그램 메타 정보 |
| `user_schedule` | 프로그램 일정 등록 정보 |
| `user_conversation_log` | 대화 내용 및 추천 이력 저장 |
| `course_personality` | 프로그램별 성향 태그 |

---
