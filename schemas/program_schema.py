from dotenv import load_dotenv
from pydantic import BaseModel, model_validator
from datetime import time
from typing import Optional, List

import os

load_dotenv()

class TagSchema(BaseModel):
    name: str

    class Config:
        from_attributes = True

class ProgramSchema(BaseModel):
    id: int
    name: str
    fir_day: str
    sec_day: str | None
    thr_day: str | None
    fou_day: str | None
    fiv_day: str | None
    start_time: time
    end_time: time
    price: int
    main_category: str
    sub_category: str
    headcount: str
    tags: list[TagSchema] | None
    image_url: Optional[str] = None

    @model_validator(mode="after")
    def add_image_url(self) -> "ProgramSchema":
        base_url = os.getenv("AWS_IMAGE_URL")
        self.image_url = f"{base_url}/{self.id}.jpg"
        return self

    class Config:
        from_attributes = True