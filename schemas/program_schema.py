from pydantic import BaseModel
from datetime import time

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

    class Config:
        from_attributes = True