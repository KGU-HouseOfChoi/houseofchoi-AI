import json
from importlib.resources import contents

# FastAPI
from fastapi import APIRouter, status
from fastapi.params import Query, Depends
from fastapi.responses import JSONResponse

from crud.chat_log import get_recent_user_messages
from crud.personality import *
from utils.database import get_db
from utils.gpt_utils import gpt_call
from schemas.personality_schema import AnalyzeResponse, AnalyzeRequest, MBTI
from utils.jwt_utils import verify_token 

personality_router = APIRouter()

# 1) 13문항 질문 (온보딩)
QUESTIONS = [
    {"id": 1,  "question": "손주가 예고 없이 찾아오면?",    "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2,  "question": "새로운 기술을 배울 때?",       "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    {"id": 3,  "question": "혼자 VS 함께?",             "choices": ["(A) 혼자가 좋다", "(B) 사람들과 함께"]},
    {"id": 4,  "question": "계획형 VS 즉흥형?",         "choices": ["(A) 미리 계획", "(B) 즉흥 결정"]},
    {"id": 5,  "question": "익숙한 장소 vs 새로운 장소?",  "choices": ["(A) 익숙한 곳", "(B) 새로운 곳"]},
    {"id": 6,  "question": "결정할 때?",              "choices": ["(A) 신중하게", "(B) 직감으로"]},
    {"id": 7,  "question": "사회적 활동?",             "choices": ["(A) 참여한다", "(B) 혼자가 좋다"]},
    {"id": 8,  "question": "변화를 좋아하는가?",         "choices": ["(A) 변화를 좋아함", "(B) 안정이 좋다"]},
    {"id": 9,  "question": "여가 시간?",              "choices": ["(A) 새로운 도전", "(B) 익숙한 활동"]},
    {"id": 10, "question": "스트레스 해소법?",           "choices": ["(A) 대화", "(B) 혼자 해결"]},
    {"id": 11, "question": "운동을 선호하시나요?",      "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 12, "question": "혼자 활동을 좋아하시나요?", "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 13, "question": "조용한 활동을 선호하시나요?", "choices": ["(A) 예", "(B) 아니요"]},
]

@personality_router.get("/questions")
def get_questions(db: Session = Depends(get_db), token_user_id: str = Depends(verify_token)):
    """
    성격 테스트 질문 목록을 반환하는 API  
    🔒 인증 필요 (JWT 토큰 필요)

    **응답 예시**
    ```json
    {
        "questions": [
            "질문 1",
            "질문 2",
            "...",
            "질문 13"
        ]
    }
    ```
    """

    if is_exist_personality(db, token_user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 성향 분석을 완료한 유저입니다."
        )

    return JSONResponse(content={"data": QUESTIONS}, status_code=status.HTTP_200_OK)

@personality_router.post("/analyze", response_model=AnalyzeResponse)
def analyze_personality(
    body: AnalyzeRequest,                          # 요청 스키마는 그대로 두되
    token_user_id: str = Depends(verify_token),    # 🔑 JWT → user_id
    db: Session = Depends(get_db),
):
    """
    사용자의 답변을 분석하여 MBTI 유형 및 추가 성격 태그를 반환하는 API  
    (이제 Body에 user_id를 보내지 않아도 됩니다)

    **요청 Body 예시**
    ```json
    {
        "answers": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "A"]
    }
    ```
    """
    answers_13 = body.answers

    # 🔍 유효성 검사
    if len(answers_13) != 13:
        raise HTTPException(400, "정확히 13개의 A/B 답변이 필요합니다.")

    # 🧠 MBTI 분석
    mbti_str, all_tags = analyze_13_answers(answers_13)
    ei, sn, tf, jp = mbti_str

    # 📝 DB 저장
    create_personality(
        db=db,
        user_id=int(token_user_id),
        ei=ei, sn=sn, tf=tf, jp=jp,
        personality_tags=all_tags,
    )

    return AnalyzeResponse(
        user_id=token_user_id,
        mbti=mbti_str,
        personality_tags=all_tags,
    )

@personality_router.get("/analysis", response_model=MBTI)
def get_user_mbti(
    token_user_id: str = Depends(verify_token),    # 🔑 JWT → user_id
    db: Session = Depends(get_db),
):
    """
    사용자의 MBTI 유형 및 추가 성격 태그를 반환합니다.  
    GET /personality/analysis   (Bearer 토큰 필요)
    """
    personality = get_latest_personality_by_user_id(db, token_user_id)
    mbti_str = f"{personality.ei}{personality.sn}{personality.tf}{personality.pj}"
    tags_list = str(personality.tag).split(",") if personality.tag else []

    return MBTI(
        user_id=token_user_id,
        ei=personality.ei,
        sn=personality.sn,
        tf=personality.tf,
        jp=personality.pj,
        mbti=mbti_str,
        personality_tags=tags_list,
    )

@personality_router.post("/analysis")
def reanalyze_mbti(
    days: int = Query(30, description="최근 N일간의 데이터를 분석 (기본값: 30일)"),
    token_user_id: str = Depends(verify_token),    # 🔑 JWT → user_id
    db: Session = Depends(get_db),
):
    """
    최근 30일(기본)의 대화내용을 바탕으로 사용자의 성향을 재분석합니다.

    GPT에게 JSON 형식으로 결과를 받아 변화가 있으면 DB를 업데이트합니다.
    """
    try:
        # 1️⃣ 최근 대화 로그 가져오기
        logs = get_recent_user_messages(db, token_user_id, days)
        if not logs:
            raise HTTPException(404, f"{days}일간 대화 기록이 없어 분석 불가")

        conversation_text = "\n".join([log.user_message for log in logs])

        # 2️⃣ GPT 프롬프트
        system_prompt = (
            "당신은 노인 복지센터 AI 분석가입니다. 최근 대화를 바탕으로 사용자의 성향 변화 여부를 분석하세요. "
            "아래 JSON 형식으로 결과를 출력하세요. 각 항목은 변경된 경우 새 값을, 변화가 없으면 'NO_CHANGE'로 출력하세요."
        )
        user_prompt = f"최근 {days}일간 사용자 대화:\n{conversation_text}"

        gpt_result = gpt_call(system_prompt, user_prompt)
        changes = json.loads(gpt_result)

        # 3️⃣ 현재 성향 로드
        current_row = get_latest_personality_by_user_id(db, token_user_id)

        # 4️⃣ 변경 적용
        def get_updated(current, change):
            return change[-1] if change.startswith("NEW_") else current

        updated_ei = get_updated(current_row.ei, changes.get("ei", "NO_CHANGE"))
        updated_sn = get_updated(current_row.sn, changes.get("sn", "NO_CHANGE"))
        updated_tf = get_updated(current_row.tf, changes.get("tf", "NO_CHANGE"))
        updated_jp = get_updated(current_row.pj, changes.get("jp", "NO_CHANGE"))

        # 변화 없으면 종료
        if (updated_ei, updated_sn, updated_tf, updated_jp) == (
            current_row.ei,
            current_row.sn,
            current_row.tf,
            current_row.pj,
        ):
            return JSONResponse(200, {"message": "성향 변화 없음"})

        # 5️⃣ DB 업데이트
        new_mbti = f"{updated_ei}{updated_sn}{updated_tf}{updated_jp}"
        new_tags = analyze_mbti_tags(new_mbti)
        tags_str = ",".join(new_tags)

        update_latest_personality_by_user_id(
            db,
            token_user_id,
            updated_ei,
            updated_sn,
            updated_tf,
            updated_jp,
            tags_str,
        )

        return JSONResponse(
            200,
            {"message": f"성향 업데이트 완료. 새 MBTI: {new_mbti}, 태그: {tags_str}"},
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"분석 중 오류 발생: {e}")

# ---------------------------
# 아래는 MBTI/온보딩 분석 로직 함수들
# ---------------------------
def analyze_13_answers(answers_13):
    if len(answers_13) != 13:
        raise ValueError("정확히 13개의 A/B 답변이 필요합니다.")
    ei, sn, tf, jp = analyze_mbti_from_10(answers_13[:10])
    mbti_str = f"{ei}{sn}{tf}{jp}"
    mbti_tags = analyze_mbti_tags(mbti_str)
    onboard_tags = analyze_onboarding_tags(answers_13[10:])
    all_tags = list(set(mbti_tags + onboard_tags))
    return mbti_str, all_tags

def analyze_mbti_from_10(answers_10):
    question_map = {
        1: ('EI', {'A': 'E', 'B': 'I'}),
        2: ('SN', {'A': 'S', 'B': 'N'}),
        3: ('EI', {'A': 'I', 'B': 'E'}),
        4: ('JP', {'A': 'J', 'B': 'P'}),
        5: ('SN', {'A': 'S', 'B': 'N'}),
        6: ('TF', {'A': 'T', 'B': 'F'}),
        7: ('EI', {'A': 'E', 'B': 'I'}),
        8: ('TF', {'A': 'F', 'B': 'T'}),
        9: ('SN', {'A': 'N', 'B': 'S'}),
        10: ('JP', {'A': 'P', 'B': 'J'})
    }
    score = {'E':0, 'I':0, 'S':0, 'N':0, 'T':0, 'F':0, 'J':0, 'P':0}
    for i, ans in enumerate(answers_10, start=1):
        dim, ab_map = question_map[i]
        if ans in ab_map:
            score[ab_map[ans]] += 1
    ei = 'E' if score['E'] >= score['I'] else 'I'
    sn = 'S' if score['S'] >= score['N'] else 'N'
    tf = 'T' if score['T'] >= score['F'] else 'F'
    jp = 'J' if score['J'] >= score['P'] else 'P'
    return ei, sn, tf, jp

def analyze_mbti_tags(mbti_str):
    tags = []
    if 'E' in mbti_str:
        tags += ["외향적", "사회적"]
    else:
        tags += ["내향적", "정적인"]

    if 'S' in mbti_str:
        tags += ["현실적", "체험형"]
    else:
        tags += ["창의적", "예술적"]

    if 'T' in mbti_str:
        tags += ["분석적", "논리적"]
    else:
        tags += ["감성적", "교류형"]

    if 'J' in mbti_str:
        tags += ["구조적", "조직적"]
    else:
        tags += ["자유로운", "유동적"]

    return tags

def analyze_onboarding_tags(answers_3):
    tags = []
    if answers_3[0] == 'A':
        tags.append("활동적")
    else:
        tags.append("정적인")
    if answers_3[1] == 'A':
        tags.append("내향적")
    else:
        tags.append("외향적")
    if answers_3[2] == 'A':
        tags.append("정적인")
    else:
        tags.append("활동적")
    return tags
