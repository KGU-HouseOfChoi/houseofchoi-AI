import datetime
import random

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from crud.personality import get_latest_personality_by_user_id
from crud.program import get_program_by_id, get_all_programs
from crud.schedule import create_schedule, existing_schedule
from crud.user import get_user_by_id
from model.program import Program
from schemas.program_schema import ProgramSchema
from schemas.recommend_schema import ScheduleRequest
from utils.database import get_db
from utils.jwt_utils import verify_token 

# 공통 유틸
def _assert_same_user(url_user_id: int | str, token_user_id: str):
    if str(url_user_id) != str(token_user_id):
        raise HTTPException(403, "토큰과 user_id가 일치하지 않습니다.")

recommend_router = APIRouter()

# 사용자 성향 기반 추천 프로그램 목록
@recommend_router.get("", response_model=List[ProgramSchema])
def get_recommend_programs(
    token_user_id: str = Depends(verify_token),  # JWT → user_id
    db: Session = Depends(get_db),
):
    """
    GET /recommend   (Authorization: Bearer <token>)
    """
    # 1) 사용자 성향 태그
    personality = get_latest_personality_by_user_id(db, token_user_id)
    user_tags = str(personality.tag).split(",")

    # 2) 프로그램 태그와 교집합 ≥ 2개인 프로그램 필터
    programs = get_all_programs(db)
    matched = [
        p for p in programs
        if len(set(user_tags) & {t.name for t in p.tags}) >= 2
    ]

    # 3) 결과 반환
    if not matched:
        return JSONResponse(
            status_code=404,
            content={"message": "사용자 성향에 맞는 프로그램이 없습니다."},
        )
    return matched

# 추천 프로그램을 일정으로 저장
@recommend_router.post("", summary="추천 일정 저장")
def save_program(
    body: ScheduleRequest,                         # 이제 body.user_id는 필요 X
    token_user_id: str = Depends(verify_token),    # JWT → user_id
    db: Session = Depends(get_db),
):
    """
    추천된 프로그램을 사용자의 일정으로 등록합니다.
    - 클라이언트는 Bearer 토큰과 program_id만 보내면 됨
    """

    # 이미 등록된 경우 등록 안되게 처리
    existing = existing_schedule(db,body.program_id, int(token_user_id))

    if existing:
        raise HTTPException(status_code=409, detail="이미 등록된 일정입니다")

    # 1) 사용자·프로그램 조회
    user = get_user_by_id(db, token_user_id)
    program = get_program_by_id(db, body.program_id)

    # 2) 일정 생성
    success = create_schedule(db, user, program, program.center)

    # 3) 응답
    if success:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "일정이 저장되었습니다."},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "일정 저장에 실패하였습니다."},
    )



def fetch_all_courses():
    """
    elderly_programs 테이블에서 모든 강좌 데이터를 가져옵니다.
    """
    pass


def get_course_personality(course_name):
    """
    course_personality 테이블에서 해당 course_name의 성향(예: '외향형', '내향형')을 조회합니다.
    """
    pass


def make_json_serializable(row):
    """
    딕셔너리 row의 값 중 datetime이나 timedelta 객체가 있으면 문자열로 변환.
    Flask jsonify로 반환하기 전에 필요한 처리를 합니다.
    """
    for key, value in row.items():
        if isinstance(value, (datetime.datetime, datetime.timedelta)):
            row[key] = str(value)
    return row

def recommend_random_program(user_id : int, db: Session=Depends(get_db)):
    """
    사용자의 personality_tags와 elderly_programs 테이블의 tags를 비교해
    교집합(중복 태그)이 2개 이상인 프로그램 중 하나를 무작위로 추천합니다.
    """
    # 1. 사용자 태그 가져오기
    personality = get_latest_personality_by_user_id(db, user_id)
    tags = str(personality.tag)
    user_tags = tags.split(",")

    # 2. 프로그램 정보 가져오기
    programs = get_all_programs(db)
    
    # 3. 프로그램 태그 매칭하기
    matched_list = []
    for program in programs:
        program_tag_names = [tag.name for tag in program.tags]
        overlap = set(user_tags) & set(program_tag_names)
        if len(overlap) >= 2:
            matched_list.append(program)

    # 4. 무작위 추천
    chosen = Program(random.choice(matched_list))
    message = (
        f"✅ 추천 프로그램이 있습니다!\n\n"
        f"📌 프로그램명: {chosen.name}\n"
        f"🏢 기관명: {chosen.center.name}\n"
        f"📍 주소: {chosen.center.address}\n"
        f"📞 연락처: {chosen.center.tel}\n"
        f"🕒 시간: {chosen.start_time} ~ {chosen.end_time}\n"
        f"💰 금액: {chosen.price}\n"
        f"🧾 카테고리: {chosen.main_category} / {chosen.sub_category}\n"
        f"👥 정원: {chosen.headcount}\n"
        f"🏷️ 태그: {chosen.tags}"
    )
    return message