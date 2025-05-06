from pydantic import BaseModel
from typing import Optional

class ScheduleRequest(BaseModel):
    program_id: int