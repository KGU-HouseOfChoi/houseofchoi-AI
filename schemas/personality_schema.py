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
    user_id: str    # TODO : 추후 ERD 확인해서 바꾸기
    ei: str
    sn: str
    tf: str
    jp: str
    mbti_str: str | None = None
    tags_list: list[str] | None = None
    created_at: str