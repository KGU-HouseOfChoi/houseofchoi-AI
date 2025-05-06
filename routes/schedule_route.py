from typing import List
import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.schedule import get_all_schedules_by_id
from schemas.schedule_schema import ScheduleResponseSchema
from utils.database import get_db
from utils.jwt_utils import verify_token

schedule_router = APIRouter(prefix="/schedule", tags=["schedule"])


@schedule_router.get("/", response_model=List[ScheduleResponseSchema])
def get_schedule(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    내 일정 목록 조회  
    (AccessToken 쿠키 인증)
    """
    return get_all_schedules_by_id(db, user_id)


# 아래 함수들은 미구현 스텁 그대로 두었습니다
def save_schedule(user_id, program_name, 요일1, 요일2, 요일3, 요일4, 요일5, 시작시간, 종료시간):
    pass


def save_conversation_log(user_id, user_message, assistant_response, recommended_program=None):
    pass


def make_json_serializable(row):
    for key, value in row.items():
        if isinstance(value, (datetime.datetime, datetime.date, datetime.timedelta)):
            row[key] = str(value)
    return row
