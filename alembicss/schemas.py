from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str
    price: int

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int

    class Config:
        orm_mode = True
