from pydantic import BaseModel

class ChatbotRequest(BaseModel):
    message: str

class ScheduleResponse(BaseModel):
    schedule: str