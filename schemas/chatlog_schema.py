from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatLogResponse(BaseModel):
    id: int
    user_message: str
    assistant_response: str
    recommended_program: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True