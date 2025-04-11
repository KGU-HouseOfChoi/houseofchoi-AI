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