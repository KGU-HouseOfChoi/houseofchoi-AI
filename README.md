# 🚀 노인 복지 챗봇 & 성향 분석 프로젝트

이 프로젝트는 **노인 복지센터**를 위한 AI 챗봇과 사용자 **성향 분석 기능**을 통합하여 제공합니다.  
GPT API를 활용해 노인 복지 프로그램을 추천하고, 사용자 성향(E/I)을 분석∙추적하여 **맞춤형 강좌**를 제안합니다.

---

## 📌 프로젝트 구조 (파일별 개요)

### 1. `main.py`
- **주요 기능**  
  - **챗봇 API** (`POST /chat`)  
    - 특정 프로그램 검색 → DB 연동  
    - 프로그램이 존재하면 안내 및 일정 등록  
    - 프로그램이 없으면 AI가 대체 프로그램 제안  
  - **모든 프로그램 추천** (`GET /recommend_all/<user_id>`)  
    - 사용자 성향(E/I)에 맞는 **모든** 프로그램 목록 반환  
  - **일정 조회** (`GET /schedule/<user_id>`)  
  - **대화 로그 조회** (`GET /chatlog/<user_id>`)

### 2. `migrate.py`
- **데이터 마이그레이션 + GPT를 통한 강좌 성향 분석 스크립트**  
  - `elderly_programs.json`을 DB(`elderly_courses`)로 옮기면서,  
  - GPT를 이용해 각 강좌가 **외향형/내향형**인지 판별 후 `course_personality` 테이블에 저장  

### 3. `personality_analysis.py`
- **설문 기반 MBTI 성향 분석** API
  - **엔드포인트**  
    1) `GET /` : 질문 목록(10개)  
    2) `POST /analyze` : A/B 답변 10개 + user_id → GPT로 E/I, S/N, T/F, J/P 판별  
    3) `GET /analysis/<user_id>` : 특정 user_id의 MBTI 조회  

### 4. `re-analytics.py`
- **최근 대화 기록 기반 성향 업데이트** API
  - `POST /analyze/<user_id>?days=30` (기본 30일)
    - DB(`user_conversation_log`)에서 최근 N일 대화 조회  
    - GPT 통해 외향(E) ↔ 내향(I) 변화 감지  
    - DB(`user_personality`) 업데이트  

---

## ✅ 기능 요약

1. **프로그램 추천**  
   - 사용자 성향(E/I)에 맞는 강좌 필터링  
   - 무작위 추천 or 전체 목록 제공 (`/recommend_all/<user_id>`)  

2. **설문 조사(10문항) 기반 MBTI 성향 파악**  
   - (E/I, S/N, T/F, J/P) → DB 저장  

3. **최근 대화 기반 성향 재분석**  
   - 30일치 로그 → GPT 분석으로 E/I 변경 시 업데이트  

4. **챗봇 대화 처리**  
   - 특정 프로그램 검색, DB 유무 확인  
   - 일정 등록, 대화 로그 저장  

---

## 🛠 설치 및 실행 방법

1. **환경 설정**  
   - `.env` 파일 생성(예: `.env.example` 참고)  
   - 아래와 같은 변수를 설정:
     ```env
     OPENAI_API_KEY=YOUR_OPENAI_KEY
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_ELDERLY_DB=elderly_db
     DB_PERSONALITY_DB=personality_db
     DB_CHARSET=utf8mb4
     ```

2. **데이터베이스 세팅**  
   - `elderly_db`, `personality_db` 생성
   - **마이그레이션**(`migrate.py`) 실행 → `elderly_programs.json`의 데이터가 DB에 저장되며, 각 강좌의 **외향형/내향형** 판별
     ```bash
     python migrate.py
     ```

3. **서버 실행**  
   - **성향 분석** (MBTI 설문) 서버 (기본포트 `5000`)
     ```bash
     python personality_analysis.py
     ```
   - **대화 로그 분석** (최근 N일) 서버 (기본포트 `5002`)
     ```bash
     python re-analytics.py
     ```
   - **챗봇 & 프로그램 추천** 서버 (기본포트 `5001`)
     ```bash
     python main.py
     ```

---

```
프로젝트/
├── main.py               # 챗봇 API (추천/일정/대화로그)
├── migrate.py            # JSON→DB & GPT 분석 (외향/내향)
├── personality_analysis.py# 설문 기반 MBTI 분석
├── re-analytics.py       # 최근 대화로 성향 업데이트
├── requirements.txt      # 패키지 목록
├── .env                  # 환경 변수 (업로드 X)
└── README.md             # 설명 문서
```

---

## 🔗 **API 상세 & 예시**

### 1) `main.py` (포트: `5001`)

#### 1-1) `POST /chat`
- **기능:** 사용자 발화(메시지)를 GPT로 처리 → 프로그램 추천/일정 등록  
- **요청 예시:**
```bash
curl -X POST "http://localhost:5001/chat" -H "Content-Type: application/json" -d '{
  "user_id": "123",
  "message": "요가 프로그램 있나요?"
}'
```
- **응답 예시 (프로그램이 있을 때):**
```json
{
  "user_id": "123",
  "recommendation": "요가 강좌가 있습니다! 위치: 서울 복지센터, 연락처: 02-1234-5678"
}
```
- **응답 예시 (프로그램이 없어 대체 추천):**
```json
{
  "user_id": "123",
  "assistant_answer": "현재 센터에는 요가가 없지만, 일반적으로 이런 프로그램이 있을 수 있어요..."
}
```

#### 1-2) `GET /recommend_all/<user_id>`
- **기능:** 사용자 E/I 성향에 맞는 모든 프로그램 목록 조회  
- **요청 예시:**
```bash
curl -X GET "http://localhost:5001/recommend_all/123"
```
- **응답 예시:**
```json
{
  "user_id": "123",
  "성향": "외향형",
  "matched_programs": [
    {
      "elderly_classroom_nm": "서울 노인복지센터",
      "location": "서울 강남구",
      "tel_num": "02-1234-5678",
      "course": "댄스교실"
    },
    {
      "elderly_classroom_nm": "부산 노인복지센터",
      "location": "부산 해운대구",
      "tel_num": "051-9876-5432",
      "course": "노래교실"
    }
  ]
}
```

#### 1-3) `GET /schedule/<user_id>`
- **기능:** 특정 user_id의 일정 목록 확인  
- **요청 예시:**
```bash
curl -X GET "http://localhost:5001/schedule/123"
```
- **응답 예시:**
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

#### 1-4) `GET /chatlog/<user_id>`
- **기능:** 사용자 대화 기록 조회  
- **요청 예시:**
```bash
curl -X GET "http://localhost:5001/chatlog/123"
```
- **응답 예시:**
```json
[
  {
    "id": 5,
    "user_id": "123",
    "user_message": "요가 프로그램 있나요?",
    "assistant_response": "요가 강좌가 있습니다! 위치: 서울 복지센터...",
    "timestamp": "2024-03-10 14:05:12"
  }
]
```

---

### 2) `personality_analysis.py` (포트: `5000`)

#### 2-1) `GET /`
- **기능:** 설문 문항(10개) 조회  
- **요청 예시:**
```bash
curl -X GET "http://localhost:5000/"
```
- **응답 예시:**
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

#### 2-2) `POST /analyze`
- **기능:** 10개 문항에 대한 A/B 응답 + user_id → GPT가 MBTI (E/I, S/N, T/F, J/P) 분석  
- **요청 예시:**
```bash
curl -X POST "http://localhost:5000/analyze" -H "Content-Type: application/json" -d '{
  "user_id": "123",
  "answers": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"]
}'
```
- **응답 예시:**
```json
{
  "user_id": "123",
  "E/I": "I",
  "S/N": "S",
  "T/F": "T",
  "J/P": "P"
}
```

#### 2-3) `GET /analysis/<user_id>`
- **기능:** 특정 user_id의 MBTI 결과 조회  
- **요청 예시:**
```bash
curl -X GET "http://localhost:5000/analysis/123"
```
- **응답 예시:**
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

### 3) `re-analytics.py` (포트: `5002`)

#### 3-1) `POST /analyze/<user_id>?days=30`
- **기능:** 최근 N일(days) 대화 로그 분석하여 E/I 성향 업데이트 (기본 30일)
- **요청 예시:**
```bash
curl -X POST "http://localhost:5002/analyze/123?days=30"
```
- **응답 예시 (내향형→외향형 변경):**
```json
{
  "message": "성향이 외향형(E)으로 업데이트되었습니다."
}
```
- **응답 예시 (변경 사항 없음):**
```json
{
  "message": "성향 변화 없음"
}
```

---

### 4) `migrate.py`
- **별도 서버**가 아닌, 데이터 마이그레이션 + GPT 분석 스크립트
- **실행 예시:**
```bash
python migrate.py
```
- **동작:**  
  - `elderly_programs.json`을 읽어 `elderly_courses` 테이블에 삽입  
  - 강좌명별로 GPT 분석 → `course_personality` 테이블에 "외향형"/"내향형" 저장  
