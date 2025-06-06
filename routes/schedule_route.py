from fastapi import APIRouter
from fastapi.params import Depends
import datetime

from typing import List

from sqlalchemy.orm import Session

from crud.schedule import get_all_schedules_by_id
from schemas.schedule_schema import ScheduleResponseSchema
from utils.database import get_db
from utils.jwt_utils import verify_token

schedule_router = APIRouter()

@schedule_router.get("", response_model=List[ScheduleResponseSchema])
def get_schedule(
    token_user_id: str = Depends(verify_token),  # JWT → user_id
    db: Session = Depends(get_db),
):
    """
    내 일정 목록 조회  
    GET /schedule   (Authorization: Bearer <token>)
    """
    schedules = get_all_schedules_by_id(db, token_user_id)
    return schedules


def save_schedule(user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간):
    """
    user_schedule 테이블에 일정 정보를 저장합니다.
    새로운 DB 스키마에서는 요일1~요일5, 시작시간, 종료시간 컬럼을 사용하며,
    프로그램 이름은 'program_name' 컬럼에 저장합니다.
    """
    pass


def save_conversation_log(user_id, user_message, assistant_response, recommended_program=None):
    """
    user_conversation_log 테이블에 대화 로그를 저장합니다.
    추천된 프로그램이 있으면 recommended_program 컬럼에 함께 저장합니다.
    """
    pass

def save_conversation_log(user_id, user_message, assistant_response, recommended_program=None):
    """
    user_conversation_log 테이블에 대화 로그를 저장합니다.
    추천된 프로그램이 있으면 recommended_program 컬럼에 함께 저장합니다.
    """
    pass


"""
    추후 response_model 적용시 해당 함수 삭제 가능
    현재 datetime 필드가 serialize 불가능
"""
def make_json_serializable(row):
    for key, value in row.items():
        if isinstance(value, (datetime.datetime, datetime.date, datetime.timedelta)):
            row[key] = str(value)
    return row