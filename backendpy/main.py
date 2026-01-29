from fastapi import FastAPI, BackgroundTasks
from multiprocessing import Process,Manager
from backendpy.emailService import send_email
from backendpy.reportService import generate_report
from backendpy.dataService import run_data_analytics

app = FastAPI()

# In-memory task status dictionary
manager = Manager()
task_status = manager.dict()

# Function to run tasks in parallel
def background_tasks(user_email, status_dict):
    tasks = [
        Process(target=send_email, args=(user_email, "Welcome!", "<h1>Welcome to Ryval-X</h1>", status_dict)),
        Process(target=generate_report, args=(user_email, status_dict)),
        Process(target=run_data_analytics, args=(user_email, status_dict))
    ]

    for t in tasks:
        t.start()
    for t in tasks:
        t.join()

    print("All background tasks completed!")

@app.post("/signup")
def signup(email: str, background_tasks_manager: BackgroundTasks):
    print(f"User {email} signed up successfully")
    
    # Initialize status
    task_status[email] = {"email": "Pending", "report": "Pending", "analytics": "Pending"}
    
    # Run background tasks
    background_tasks_manager.add_task(background_tasks, email, task_status[email])
    
    return {"message": "Signup successful. Background tasks started."}

@app.get("/task-status")
def get_task_status(email: str):
    if email in task_status:
        return {"status": task_status[email]}
    return {"status": "No tasks found for this email"}
