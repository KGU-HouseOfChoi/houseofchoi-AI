from typing import Type

from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.program import Program

def get_program_by_id(db: Session, program_id: int) -> Type[Program]:
    program = db.get(Program, program_id)

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    return program