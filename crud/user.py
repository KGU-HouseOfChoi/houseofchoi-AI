from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.user import User

def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user