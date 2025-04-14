from pydantic import BaseModel


class CenterSchema(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    address: str
    tel: str

    class Config:
        from_attributes = True
