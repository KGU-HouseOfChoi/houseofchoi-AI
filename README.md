---

# 🧠 노인복지 GPT 챗봇 API

GPT를 기반으로 한 노인복지 프로그램 추천 챗봇 API입니다.  
사용자 성향을 분석하고, 맞춤형 프로그램을 추천하며, 일정 등록까지 지원합니다.

---

## 📦 주요 기능 요약

| 기능 | 설명 |
|------|------|
| 온보딩 질문 | 사용자의 성향(MBTI, 활동 성향 등)을 추출 |
| 프로그램 추천 | 사용자 성향 기반 복지 프로그램 추천 |
| 감성 대화 | 복지 관련 없는 대화는 말벗처럼 응답 |
| 일정 등록 | 추천된 프로그램을 일정으로 저장 |
| 대화 기록 | 사용자의 모든 발화를 저장하고 분석 가능 |

---

## 🚀 실행 방법

### 📌 venv로 실행하는 경우
```bash
# 환경 설정
cp .env.example .env

# 패키지 설치
pip install -r requirements.txt

# 실행
python main.py
```

### 📌 **docker로 실행하는 경우**
```bash
# 도커 컴포즈 실행
docker-compose up -d
```

---

## 📌 API 목록

### ✅ 1. 온보딩 질문 목록 조회

```
GET /questions
```

**응답 예시**
```json
{
  "questions": [
    {
      "id": 1,
      "question": "손주가 예고 없이 찾아오면?",
      "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]
    },
    ...
  ]
}
```

---

### ✅ 2. 온보딩 답변 분석 및 저장

```
POST /analyze
```

**요청 바디**
```json
{
  "user_id": "101",
  "answers": ["A", "B", ..., "A"]  // 총 13개 A/B 답변
}
```

**응답 예시**
```json
{
  "user_id": "101",
  "mbti": "ENFP",
  "personality_tags": ["외향적", "사회적", "활동적", ...]
}
```

---

### ✅ 3. 성향 기반 전체 프로그램 추천

```
GET /recommend_all/<user_id>
```

**응답 예시**
```json
{
  "user_id": 101,
  "matched_programs": [
    {
      "프로그램명": "서예교실",
      "기관명": "SK노인복지관",
      "tags": "감성적, 창의적, 정적인",
      ...
    }
  ]
}
```

---

### ✅ 4. GPT 챗봇 대화 요청

```
POST /chat
```

**요청 바디**
```json
{
  "user_id": "101",
  "message": "요가 프로그램 있나요?"
}
```

**응답 예시 (프로그램 존재 시)**  
```json
{
  "user_id": "101",
  "recommendation": "네, SK복지관에서 요가 수업이 진행 중이에요. 등록하시겠어요?",
  "recommended_program": "요가"
}
```

**응답 예시 (감성 대화)**  
```json
{
  "user_id": "101",
  "assistant_answer": "요즘 많이 힘드셨겠어요. 제가 곁에 있어드릴게요."
}
```

---

### ✅ 5. 추천된 프로그램 일정 등록

**조건**: 사용자가 `"예"`, `"등록"` 등 의사 표현  
→ 내부적으로 가장 최근 추천된 프로그램을 기반으로 등록

**응답 예시**
```json
{
  "user_id": "101",
  "schedule": "✅ '서예교실' 일정이 등록되었습니다!"
}
```

---

### ✅ 6. 사용자 일정 조회

```
GET /schedule/<user_id>
```

**응답 예시**
```json
[
  {
    "program_name": "서예교실",
    "요일1": "화",
    "요일3": "목",
    "시작시간": "10:00",
    "종료시간": "12:00",
    ...
  }
]
```

---

### ✅ 7. 사용자 성향 분석 조회

```
GET /analysis/<user_id>
```

**응답 예시**
```json
{
  "user_id": 101,
  "mbti": "ENFP",
  "personality_tags": ["외향적", "창의적", "감성적"],
  "created_at": "2025-03-22 10:12:00"
}
```

---

### ✅ 8. 최근 대화 기반 성향 변화 분석

```
POST /analyze/<user_id>?days=30
```

**응답 예시**
```json
{
  "message": "성향 업데이트 완료. 새 MBTI: ISFJ, 태그: 내향적, 현실적, 감성적, 구조적"
}
```

---

### ✅ 9. 사용자 대화 로그 조회

```
GET /chatlog/<user_id>
```

**응답 예시**
```json
[
  {
    "user_id": 101,
    "user_message": "요즘 너무 외로워요",
    "assistant_response": "제가 항상 곁에 있어요. 언제든지 말 걸어주세요.",
    "timestamp": "2025-03-22T10:13:45"
  },
  ...
]
```

---

## 📋 .env 환경 변수

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=capstone
DB_CHARSET=utf8mb4

OPENAI_API_KEY=sk-...
```

---

## 🧱 DB 테이블 주요 구조

| 테이블명 | 설명 |
|----------|------|
| `user_personality` | MBTI, 태그, 사용자 성향 정보 저장 |
| `elderly_programs` | 복지 프로그램 정보 저장 |
| `user_schedule` | 프로그램 일정 등록 정보 |
| `user_conversation_log` | 대화 내용, 추천 프로그램 로그 |
| `course_personality` | (선택적) 강좌별 성향 정보 |

---
