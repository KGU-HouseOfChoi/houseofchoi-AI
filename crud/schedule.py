from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
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


def get_schedules_by_user_id(db: Session, user_id: int) -> list[ScheduleResponseSchema]:
    schedules = (
        db.query(Schedule)
        .options(joinedload(Schedule.program), joinedload(Schedule.center))
        .filter(Schedule.user_id == user_id)
        .order_by(Schedule.created_at.desc())
        .all()
    )

    if not schedules:
        raise HTTPException(status_code=404, detail="등록된 스케줄 정보를 찾을 수 없습니다.")

    return [ScheduleResponseSchema.from_orm(schedule) for schedule in schedules]