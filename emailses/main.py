from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from .emailService import send_welcome_email

app = FastAPI(title="Signup with Welcome Email")


# Fake DB (for demo purpose)
users_db = set()  # stores registered emails

# Request model

class SignupRequest(BaseModel):
    email: str
    password: str

# Signup API
@app.post("/signup")
async def signup(user: SignupRequest, background_tasks: BackgroundTasks):

    # Check if user already exists
    if user.email in users_db:
        return {
            "message": "User already exists",
            "email_status": "Welcome email NOT sent"
        }

    #  First time user → create user
    users_db.add(user.email)
    print("NEW USER CREATED:", user.email)

    # Send welcome email ONLY ONCE (background)
    background_tasks.add_task(send_welcome_email, user.email)

    return {
        "message": "Signup successful",
        "email_status": "Welcome email will be sent in background"
    }
