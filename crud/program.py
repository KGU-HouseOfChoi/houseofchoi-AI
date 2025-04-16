from typing import List, Type

from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.program import Program

def get_program_by_name(db: Session, program_name: str) -> Program:
    program = db.query(Program).filter(Program.name == program_name).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    return program

def get_program_by_id(db: Session, program_id: int) -> Type[Program]:
    program = db.get(Program, program_id)

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    return program

def get_program_by_keyword(db: Session, keyword: str) -> list[Type[Program]]:
    program = db.query(Program).filter(Program.name.like(f"%{keyword}")).all()

    return program