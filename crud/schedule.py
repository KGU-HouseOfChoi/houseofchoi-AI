from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.schedule import Schedule
from model.user import User
from model.program import Program
from model.center import Center

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
