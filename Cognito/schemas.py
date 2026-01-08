from pydantic import BaseModel

class PostCreate(BaseModel):
    
    content: str
    user_id: int

class PostResponse(PostCreate):
    id: int

    class Config:
        from_attributes = True
