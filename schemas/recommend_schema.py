from pydantic import BaseModel
from typing import Optional

class ScheduleRequest(BaseModel):
    user_id: int
    program_id: int