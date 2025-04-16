from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class ChatbotRequest(BaseModel):
    user_id: str
    message: str

class ScheduleResponse(BaseModel):
    user_id: str
    schedule: str