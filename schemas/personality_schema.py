from datetime import datetime

from pydantic import BaseModel
from typing import List

class AnalyzeRequest(BaseModel):
    answers: List[str]

class AnalyzeResponse(BaseModel):
    mbti: str
    personality_tags: List[str]

class MBTI(BaseModel):
    ei: str
    sn: str
    tf: str
    jp: str
    mbti: str
    personality_tags: List[str]