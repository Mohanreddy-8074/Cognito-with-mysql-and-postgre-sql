from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cognito API")

users_db = {}

class User(BaseModel):
    name: str
    role: str

# ---------------- BASIC APIs ----------------
@app.get("/")
def root():
    return {"message": "Cognito API is running"}

@app.get("/health")
def health():
    return {"status": "OK"}

@app.post("/login")
def login():
    return {"token": "dummy-token"}

# ---------------- CRUD APIs ----------------
@app.post("/users/{user_id}")
def create_user(user_id: int, user: User):
    users_db[user_id] = user.model_dump()
    return users_db[user_id]

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    users_db[user_id] = user.model_dump()
    return users_db[user_id]

@app.patch("/users/{user_id}")
def patch_user(user_id: int, role: str):
    users_db[user_id]["role"] = role
    return users_db[user_id]

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    del users_db[user_id]
    return {"message": "User deleted successfully"}
