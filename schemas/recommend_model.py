from pydantic import BaseModel
from typing import Optional

class ScheduleRequest(BaseModel):
    user_id: int
    program_name: str
    start_time: str
    end_time: str
    day1: Optional[str] = None
    day2: Optional[str] = None
    day3: Optional[str] = None
    day4: Optional[str] = None
    day5: Optional[str] = None