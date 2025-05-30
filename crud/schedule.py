from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from model.schedule import Schedule
from model.user import User
from model.program import Program
from model.center import Center
from schemas.schedule_schema import ScheduleResponseSchema


def create_schedule(
    db: Session,
    user: User,
    program: Program,
    center: Center
) -> Schedule:
    schedule = Schedule(user=user, program=program, center=center)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

def get_all_schedules_by_id(db: Session, user_id: int) -> List[Schedule]:
    schedules = db.query(Schedule).filter_by(user_id=user_id).all()

    if not schedules:
        raise HTTPException(status_code=404, detail="등록된 스케줄이 없습니다.")

    return schedules

def existing_schedule(db: Session, user_id: int, program_id: int):
    existing = db.query(Schedule).filter_by(user_id=user_id, program_id=program_id).first()

    if existing:
        raise HTTPException(status_code=409, detail="이미 등록된 일정입니다.")

    return existing
