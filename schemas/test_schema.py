from pydantic import BaseModel

class ScheduleCreateRequest(BaseModel):
    user_id: int
    program_id: int