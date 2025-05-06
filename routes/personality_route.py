# routes/personality_route.py
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from crud.chat_log import get_recent_user_messages
from crud.personality import (
    create_personality,
    get_latest_personality_by_user_id,
    update_latest_personality_by_user_id,
)
from schemas.personality_schema import AnalyzeRequest, AnalyzeResponse, MBTI
from utils.database import get_db
from utils.gpt_utils import gpt_call
from utils.jwt_utils import verify_token  # 쿠키 전용 verify_token

personality_router = APIRouter(prefix="/personality", tags=["personality"])

# ────────────────────────────────────────────────
# 온보딩 13문항
# ────────────────────────────────────────────────
QUESTIONS = [
    {"id": 1,  "question": "손주가 예고 없이 찾아오면?",     "choices": ["(A) 반갑다", "(B) 미리 연락이 좋다"]},
    {"id": 2,  "question": "새로운 기술을 배울 때?",        "choices": ["(A) 직접 시도", "(B) 도움 요청"]},
    {"id": 3,  "question": "혼자 VS 함께?",              "choices": ["(A) 혼자가 좋다", "(B) 사람들과 함께"]},
    {"id": 4,  "question": "계획형 VS 즉흥형?",          "choices": ["(A) 미리 계획", "(B) 즉흥 결정"]},
    {"id": 5,  "question": "새로운 장소 vs 익숙한 장소?",   "choices": ["(A) 익숙한 곳", "(B) 새로운 곳"]},
    {"id": 6,  "question": "결정할 때?",               "choices": ["(A) 신중하게", "(B) 직감으로"]},
    {"id": 7,  "question": "사회적 활동?",              "choices": ["(A) 참여한다", "(B) 혼자가 좋다"]},
    {"id": 8,  "question": "변화를 좋아하는가?",          "choices": ["(A) 변화를 좋아함", "(B) 안정이 좋다"]},
    {"id": 9,  "question": "여가 시간?",               "choices": ["(A) 새로운 도전", "(B) 익숙한 활동"]},
    {"id": 10, "question": "스트레스 해소법?",            "choices": ["(A) 대화", "(B) 혼자 해결"]},
    {"id": 11, "question": "운동을 선호하시나요?",       "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 12, "question": "혼자 활동을 좋아하시나요?",  "choices": ["(A) 예", "(B) 아니요"]},
    {"id": 13, "question": "조용한 활동을 선호하시나요?",  "choices": ["(A) 예", "(B) 아니요"]},
]

# ────────────────────────────────────────────────
# 온보딩 분석
# ────────────────────────────────────────────────
@personality_router.post("/analyze", response_model=AnalyzeResponse)
def analyze_personality(
    body: AnalyzeRequest,
    user_id: str = Depends(verify_token),   # AccessToken 쿠키 → user_id
    db: Session = Depends(get_db),
):
    """13문항 답변을 기반으로 성향 저장 및 반환"""
    answers = body.answers
    if len(answers) != 13:
        raise HTTPException(400, "정확히 13개의 A/B 답변이 필요합니다.")

    mbti_str, all_tags = analyze_13_answers(answers)
    ei, sn, tf, jp = mbti_str

    create_personality(
        db,
        user_id=int(user_id),
        ei=ei, sn=sn, tf=tf, jp=jp,
        personality_tags=all_tags,
    )

    return AnalyzeResponse(
        user_id=user_id,
        mbti=mbti_str,
        personality_tags=all_tags,
    )

# ────────────────────────────────────────────────
# 최신 성향 조회
# ────────────────────────────────────────────────
@personality_router.get("/analysis", response_model=MBTI)
def get_user_mbti(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """사용자의 최신 MBTI 및 태그 반환 (AccessToken 쿠키 인증)"""
    personality = get_latest_personality_by_user_id(db, user_id)
    mbti_str = f"{personality.ei}{personality.sn}{personality.tf}{personality.pj}"
    tags = str(personality.tag).split(",") if personality.tag else []

    return MBTI(
        user_id=user_id,
        ei=personality.ei,
        sn=personality.sn,
        tf=personality.tf,
        jp=personality.pj,
        mbti=mbti_str,
        personality_tags=tags,
    )

# ────────────────────────────────────────────────
# 최근 대화 기반 재분석
# ────────────────────────────────────────────────
@personality_router.post("/analysis")
def reanalyze_mbti(
    days: int = Query(30, description="최근 N일간 대화 분석"),
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        logs = get_recent_user_messages(db, user_id, days)
        if not logs:
            raise HTTPException(404, f"{days}일간 대화 기록이 없습니다.")

        convo = "\n".join(l.user_message for l in logs)
        sys_prompt = (
            "당신은 노인 복지센터 AI 분석가입니다. 최근 대화로 성향 변화 여부를 분석하세요. "
            "아래 JSON 형식으로 출력하세요."
        )
        gpt_json = gpt_call(sys_prompt, f"최근 {days}일 대화:\n{convo}")
        changes = json.loads(gpt_json)

        cur = get_latest_personality_by_user_id(db, user_id)

        def updated(cur_val, change_val):
            return change_val[-1] if change_val.startswith("NEW_") else cur_val

        new_ei = updated(cur.ei, changes.get("ei", "NO_CHANGE"))
        new_sn = updated(cur.sn, changes.get("sn", "NO_CHANGE"))
        new_tf = updated(cur.tf, changes.get("tf", "NO_CHANGE"))
        new_jp = updated(cur.pj, changes.get("jp", "NO_CHANGE"))

        if (new_ei, new_sn, new_tf, new_jp) == (cur.ei, cur.sn, cur.tf, cur.pj):
            return JSONResponse(200, {"message": "성향 변화 없음"})

        new_mbti = f"{new_ei}{new_sn}{new_tf}{new_jp}"
        new_tags = ",".join(analyze_mbti_tags(new_mbti))

        update_latest_personality_by_user_id(
            db, user_id, new_ei, new_sn, new_tf, new_jp, new_tags
        )

        return JSONResponse(
            200,
            {"message": f"업데이트 완료 ▶ MBTI {new_mbti}, 태그 {new_tags}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"분석 중 오류: {e}")

# ────────────────────────────────────────────────
# MBTI / 온보딩 분석 로직
# ────────────────────────────────────────────────
def analyze_13_answers(answers_13: List[str]):
    ei, sn, tf, jp = analyze_mbti_from_10(answers_13[:10])
    mbti_str = f"{ei}{sn}{tf}{jp}"
    tags = list(set(analyze_mbti_tags(mbti_str) + analyze_onboarding_tags(answers_13[10:])))
    return mbti_str, tags


def analyze_mbti_from_10(ans_10):
    qmap = {
        1: ('EI', {'A': 'E', 'B': 'I'}),
        2: ('SN', {'A': 'S', 'B': 'N'}),
        3: ('EI', {'A': 'I', 'B': 'E'}),
        4: ('JP', {'A': 'J', 'B': 'P'}),
        5: ('SN', {'A': 'S', 'B': 'N'}),
        6: ('TF', {'A': 'T', 'B': 'F'}),
        7: ('EI', {'A': 'E', 'B': 'I'}),
        8: ('TF', {'A': 'F', 'B': 'T'}),
        9: ('SN', {'A': 'N', 'B': 'S'}),
        10: ('JP', {'A': 'P', 'B': 'J'}),
    }
    score = {k: 0 for k in "EISNTFJP"}
    for i, ans in enumerate(ans_10, 1):
        dim, amap = qmap[i]
        if ans in amap:
            score[amap[ans]] += 1
    ei = 'E' if score['E'] >= score['I'] else 'I'
    sn = 'S' if score['S'] >= score['N'] else 'N'
    tf = 'T' if score['T'] >= score['F'] else 'F'
    jp = 'J' if score['J'] >= score['P'] else 'P'
    return ei, sn, tf, jp


def analyze_mbti_tags(mbti):
    tags = []
    tags += ["외향적", "사회적"] if 'E' in mbti else ["내향적", "정적인"]
    tags += ["현실적", "체험형"]  if 'S' in mbti else ["창의적", "예술적"]
    tags += ["분석적", "논리적"]  if 'T' in mbti else ["감성적", "교류형"]
    tags += ["구조적", "조직적"]  if 'J' in mbti else ["자유로운", "유동적"]
    return tags


def analyze_onboarding_tags(ans3):
    t = []
    t.append("활동적" if ans3[0] == 'A' else "정적인")
    t.append("내향적" if ans3[1] == 'A' else "외향적")
    t.append("정적인" if ans3[2] == 'A' else "활동적")
    return t
