from typing import Type

from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.center import Center

def get_center_by_id(db: Session, center_id: int) -> Type[Center]:
    center = db.query(Center).filter_by(id=center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    return center