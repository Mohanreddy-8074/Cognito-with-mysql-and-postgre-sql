from fastapi import FastAPI, BackgroundTasks
import asyncio
import os

app = FastAPI()

# Async I/O task
async def send_email(email: str):
    print(f"[PID {os.getpid()}] Sending email to {email}")
    await asyncio.sleep(2)
    print("Email sent")

# Async CPU-like task (simulated)
async def heavy_analytics(email: str):
    print(f"[PID {os.getpid()}] Running analytics for {email}")
    await asyncio.sleep(5)
    print(f"[PID {os.getpid()}] Analytics done for {email}")

# Async background job
async def background_job(email: str):
    await send_email(email)
    await heavy_analytics(email)
    print("All background tasks completed!")

@app.post("/signup")
async def signup(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_job, email)
    return {"message": "Signup successful, async tasks running in background"}
