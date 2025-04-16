import json
import pymysql

# FastAPI
from fastapi import APIRouter, status
from fastapi.params import Query, Depends
from fastapi.responses import JSONResponse

from crud.chat_log import get_recent_user_messages
from crud.personality import *
from utils.database import get_db
from utils.db_utils import get_capstone_db_connection  # DB 연결 함수 (예: capstone DB)
from utils.gpt_utils import gpt_call
from schemas.personality_schema import AnalyzeResponse, AnalyzeRequest, MBTI

personality_router = APIRouter()

# 1) 13문항 질문 (온보딩)
QUESTIONS = [
    {"id": 1,  "question": "손주가 예고 없이 찾아오면?",    "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2,  "question": "새로운 기술을 배울 때?",       "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    {"id": 3,  "question": "혼자 VS 함께?",             "choices": ["(A) 혼자가 좋다", "(B) 사람들과 함께"]},
    {"id": 4,  "question": "계획형 VS 즉흥형?",         "choices": ["(A) 미리 계획", "(B) 즉흥 결정"]},
    {"id": 5,  "question": "새로운 장소 vs 익숙한 장소?",  "choices": ["(A) 익숙한 곳", "(B) 새로운 곳"]},
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
def get_questions():
    """
    성격 테스트 질문 목록을 반환하는 API

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
    return JSONResponse(
        content=QUESTIONS, status_code=status.HTTP_200_OK
    )

@personality_router.post("/analyze", response_model=AnalyzeResponse)
def post(body: AnalyzeRequest, db:Session=Depends(get_db)):
    """
    사용자의 답변을 분석하여 MBTI 유형 및 추가 성격 태그를 반환하는 API

    **요청 Body 예시**
    ```json
    {
        "user_id": "12345",
        "answers": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "A"]
    }
    ```

    **응답 예시**
    ```json
    {
        "user_id": "12345",
        "mbti": "INTP",
        "personality_tags": ["논리적", "분석적", "창의적"]
    }
    ```

    **오류 응답 예시**
    ```json
    {
        "error": "정확히 13개의 A/B 답변이 필요합니다."
    }
    ```
    """
    user_id = body.user_id
    answers_13 = body.answers

    # 유효성 검사
    if len(answers_13) != 13:
        raise HTTPException(status_code=400, detail="정확히 13개의 A/B 답변이 필요합니다.")

    try:
        mbti_str, all_tags = analyze_13_answers(answers_13)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ei, sn, tf, jp = mbti_str[0], mbti_str[1], mbti_str[2], mbti_str[3]
    create_personality(db, int(user_id), ei, sn, tf, jp, all_tags)

    return AnalyzeResponse(
        user_id=user_id,
        mbti=mbti_str,
        personality_tags=all_tags
    )

@personality_router.get("/analysis/{user_id}", response_model=MBTI)
def get_user_mbti(user_id: int, db:Session=Depends(get_db)):
    """
    사용자의 MBTI 유형 및 추가 성격 태그를 반환합니다.

    :param user_id:
    :param db:
    :return:
    ```json
    {
        "user_id": row["user_id"],
        "ei": row["ei"],
        "sn": row["sn"],
        "tf": row["tf"],
        "jp": row["jp"],
        "mbti": mbti_str,
        "personality_tags": tags_list,
        "created_at": str(row["created_at"])
    }
    ```
    """

    personality = get_latest_personality_by_user_id(db, user_id)
    mbti_str = f"{personality.ei}{personality.sn}{personality.tf}{personality.pj}"
    tags_list = str(personality.tag).split(',') if personality.tag else []

    return MBTI(
        user_id=str(personality.user_id),
        ei=str(personality.ei),
        sn=str(personality.sn),
        tf=str(personality.tf),
        jp=str(personality.pj),
        mbti=mbti_str,
        personality_tags=tags_list,
    )

@personality_router.post("/analysis/{user_id}")
def post(
        user_id: int,
        days: int = Query(30, description="최근 N일간의 데이터를 분석 (기본값: 30일)"),
        db:Session=Depends(get_db),
):
    """
    최근 30일의 대화내용을 바탕으로 사용자의 성향을 재분석합니다.

    최근 N일(기본 30일)간의 대화 로그를 기반으로, 사용자의 성향 변화(각 축: ei, sn, tf, jp)를 분석하여
    변화가 감지되면 DB의 해당 필드와 태그(personality_tags)를 업데이트합니다.

    GPT에게 아래와 같이 JSON 형식으로 응답하도록 요청합니다:
    ```
    {
      "ei": "NEW_E" 또는 "NEW_I" 또는 "NO_CHANGE",
      "sn": "NEW_S" 또는 "NEW_N" 또는 "NO_CHANGE",
      "tf": "NEW_T" 또는 "NEW_F" 또는 "NO_CHANGE",
      "jp": "NEW_J" 또는 "NEW_P" 또는 "NO_CHANGE"
    }
    ```
    """
    try:
        logs = get_recent_user_messages(db, user_id, days)
        if not logs:
            return HTTPException(
                status_code=404,
                detail=f"{days}일간 대화 기록이 없어 분석 불가"
            )
        conversation_text = "\n".join([log.user_message for log in logs])

        system_prompt = (
            "당신은 노인 복지센터 AI 분석가입니다. 최근 대화를 바탕으로 사용자의 성향 변화 여부를 분석하세요. "
            "아래 JSON 형식으로 결과를 출력하세요. 각 항목은 변경된 경우 새 값을, 변화가 없으면 'NO_CHANGE'로 출력하세요.\n"
            "{\n"
            '  "ei": "NEW_E" 또는 "NEW_I" 또는 "NO_CHANGE",\n'
            '  "sn": "NEW_S" 또는 "NEW_N" 또는 "NO_CHANGE",\n'
            '  "tf": "NEW_T" 또는 "NEW_F" 또는 "NO_CHANGE",\n'
            '  "jp": "NEW_J" 또는 "NEW_P" 또는 "NO_CHANGE"\n'
            "}\n"
            "예를 들어, 만약 대화에서 내향적 성향이 강화되면 {\"ei\": \"NEW_I\", \"sn\": \"NO_CHANGE\", \"tf\": \"NO_CHANGE\", \"jp\": \"NO_CHANGE\"}와 같이 응답하세요."
        )
        user_prompt = f"최근 {days}일간 사용자 대화:\n{conversation_text}"

        gpt_result = gpt_call(system_prompt, user_prompt)
        print("[DEBUG] GPT 분석 결과:", gpt_result)

        try:
            changes = json.loads(gpt_result)
        except Exception as e:
            return HTTPException(
                status_code=500,
                detail=f"GPT 결과 JSON 파싱 실패\n오류 내용{str(e)}"
            )

        # 현재 DB에 저장된 성향 조회
        current_row = get_latest_personality_by_user_id(db, user_id)
        if not current_row:
            return HTTPException(
                status_code=404,
                detail=f"{user_id} 사용자의 기존 성향 데이터가 없습니다."
            )

        # 각 성향 업데이트 결정 (NEW_ 접두사가 있으면 새 값, NO_CHANGE면 현재 값 유지)
        def get_updated(current, change):
            if change.startswith("NEW_"):
                return change[-1]  # 마지막 문자(E, I, S, N, T, F, J, P)
            return current

        updated_ei = get_updated(current_row.ei, changes.get("ei", "NO_CHANGE"))
        updated_sn = get_updated(current_row.sn, changes.get("sn", "NO_CHANGE"))
        updated_tf = get_updated(current_row.tf, changes.get("tf", "NO_CHANGE"))
        updated_jp = get_updated(current_row.pj, changes.get("jp", "NO_CHANGE"))

        # 만약 아무 것도 변경되지 않았다면
        if (updated_ei == current_row.ei and updated_sn == current_row.sn and
            updated_tf == current_row.tf and updated_jp == current_row.pj):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "성향 변화 없음"
                }
            )

        # 새 MBTI 문자열 생성
        new_mbti = f"{updated_ei}{updated_sn}{updated_tf}{updated_jp}"
        # 업데이트된 태그 재계산 (analyze_mbti_tags 함수 사용; 해당 함수는 아래에 정의됨)
        new_tags = analyze_mbti_tags(new_mbti)
        tags_str = ",".join(new_tags)

        latest_personality = update_latest_personality_by_user_id(
            db, user_id, updated_ei, updated_sn, updated_tf, updated_jp, tags_str
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"성향 업데이트 완료. 새 MBTI: {new_mbti}, 태그: {tags_str}"
            }
        )
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        return HTTPException(
            status_code=500,
            detail="분석 중 오류 발생"
        )
    finally:
        pass

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
