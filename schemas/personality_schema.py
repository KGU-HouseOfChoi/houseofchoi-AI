from datetime import datetime

from pydantic import BaseModel
from typing import List

class AnalyzeRequest(BaseModel):
    user_id: str
    answers: List[str]

class AnalyzeResponse(BaseModel):
    user_id: str
    mbti: str
    personality_tags: List[str]

class MBTI(BaseModel):
    user_id: str
    ei: str
    sn: str
    tf: str
    jp: str
    mbti: str
    personality_tags: List[str]