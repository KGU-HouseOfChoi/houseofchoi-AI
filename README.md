# 🚀 노인 복지 챗봇 API 및 성향 분석 기능

## 📌 프로젝트 개요 (Overview)
이 프로젝트는 **노인 복지 챗봇 API 및 성향 분석 기능**을 제공합니다.  
사용자의 성향을 기반으로 맞춤 프로그램을 추천하고, 일정 등록 및 대화 로그를 관리하는 기능을 포함합니다.  
또한, 최근 대화 기록을 분석하여 성향(E/I)을 업데이트하는 기능을 제공합니다.  

---

## ✅ 주요 기능 (Features)

### 1️⃣ **Flask 기반 챗봇 API**
- **MySQL 연동 (`elderly_db`, `personality_db`)**
- **GPT API를 활용한 대화 생성 및 성향 분석**

### 2️⃣ **노인 복지 프로그램 추천**
- 사용자 성향(E/I)에 따른 맞춤 프로그램 추천
- 특정 프로그램 검색 및 안내 (없을 시 GPT 활용)
- 일정 등록 및 조회 기능 제공

### 3️⃣ **GPT 기반 성향 분석**
- 설문(10개 문항) 기반 MBTI 성향 분석 API (`/analyze`)
- 최근 30일 대화 기록을 바탕으로 성향(E/I) 업데이트 (`/analyze/<user_id>`)

---

## 📌 API 엔드포인트 (Endpoints) 및 예제 요청

### 📍 1) **기본 엔드포인트**
#### 1-1. 질문 목록 조회
- **Endpoint:** `GET /`
- **설명:** 설문 질문 목록을 JSON 형태로 반환

##### ✅ 요청 예시:
```bash
curl -X GET "http://localhost:5000/"
```
##### ✅ 응답 예시:
```json
{
  "questions": [
    {"id": 1, "question": "손주가 예고 없이 찾아오면?", "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2, "question": "새로운 기술을 배울 때?", "choices": ["(A) 직접 시도", "(B) 도움 요청"]}
  ]
}
```

#### 1-2. 챗봇 대화 처리
- **Endpoint:** `POST /chat`
- **설명:** 사용자 메시지를 기반으로 프로그램 추천 또는 정보 제공

##### ✅ 요청 예시:
```bash
curl -X POST "http://localhost:5001/chat" -H "Content-Type: application/json" -d '{
  "user_id": "123",
  "message": "요가 강좌 있나요?"
}'
```
##### ✅ 응답 예시:
```json
{
  "user_id": "123",
  "recommendation": "요가 강좌가 있습니다! 위치: 서울 복지센터, 연락처: 02-1234-5678"
}
```

---

### 📍 2) **일정 관리**
#### 2-1. 일정 조회
- **Endpoint:** `GET /schedule/<user_id>`
- **설명:** 특정 사용자의 일정 목록 조회

##### ✅ 요청 예시:
```bash
curl -X GET "http://localhost:5001/schedule/123"
```
##### ✅ 응답 예시:
```json
[
  {
    "schedule_id": 1,
    "user_id": "123",
    "program_name": "요가 강좌",
    "schedule_time": null,
    "created_at": "2024-03-10 14:00:00"
  }
]
```

---

### 📍 3) **사용자 성향 분석 및 조회**
#### 3-1. 설문 기반 성향 분석
- **Endpoint:** `POST /analyze`
- **설명:** 10개 문항의 A/B 선택 결과를 기반으로 GPT 분석 후 성향 저장

##### ✅ 요청 예시:
```bash
curl -X POST "http://localhost:5000/analyze" -H "Content-Type: application/json" -d '{
  "user_id": "123",
  "answers": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"]
}'
```
##### ✅ 응답 예시:
```json
{
  "user_id": "123",
  "E/I": "I",
  "S/N": "S",
  "T/F": "T",
  "J/P": "P"
}
```

---

#### 3-2. 특정 사용자 성향 조회
- **Endpoint:** `GET /analysis/<user_id>`
- **설명:** 특정 사용자의 MBTI 분석 결과를 조회  

##### ✅ 요청 예시:
```bash
curl -X GET "http://localhost:5000/analysis/123"
```
##### ✅ 응답 예시:
```json
{
  "user_id": "123",
  "E/I": "I",
  "S/N": "S",
  "T/F": "T",
  "J/P": "P",
  "created_at": "2024-03-10 14:00:00"
}
```

---

### 📍 4) **최근 대화 기반 성향 업데이트**
#### 4-1. 사용자 최근 대화 분석하여 성향 업데이트
- **Endpoint:** `POST /analyze/<user_id>`
- **설명:** 최근 30일 대화를 분석하여 사용자의 성향(E/I) 업데이트

##### ✅ 요청 예시:
```bash
curl -X POST "http://localhost:5002/analyze/123"
```
##### ✅ 응답 예시:
```json
{
  "message": "성향이 외향형(E)으로 업데이트되었습니다."
}
```

---

## 🛠 **설치 및 실행 방법 (How to Run)**

### 1️⃣ **환경 설정**
- `.env` 파일을 생성하고 아래 정보를 입력:
  ```
  OPENAI_API_KEY=your_api_key
  DB_HOST=localhost
  DB_USER=root
  DB_PASSWORD=your_password
  DB_NAME=personality_db
  ```

### 2️⃣ **MySQL 데이터베이스 설정**
- `elderly_db` 및 `personality_db` 생성  
- `user_personality`, `user_conversation_log`, `elderly_courses` 등의 테이블을 준비  

### 3️⃣ **서버 실행**
```bash
# 챗봇 API 실행 (포트 5001)
python app.py  

# 성향 분석 API 실행 (포트 5002)
python analyze.py  
```

---

## 🔗 **연관 이슈 (Related Issues)**
- #1 **노인 복지 챗봇 API 개발**
- #2 **OpenAI API 연동 및 성향 분석 기능 개선**

---

