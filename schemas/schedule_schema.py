from pydantic import BaseModel
from datetime import datetime

from schemas.center_schema import CenterSchema
from schemas.program_schema import ProgramSchema


class ScheduleResponseSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    program: ProgramSchema
    center: CenterSchema

    class Config:
        from_attributes = True
