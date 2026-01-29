import time
import random

def run_data_analytics(user_email, status_dict):
    status_dict["analytics"] = "Running"
    print(f"Running data analytics for {user_email}...")
    time.sleep(4)
    result = random.randint(1, 100)
    with open("analytics_results.txt", "a") as f:
        f.write(f"{user_email}: {result}\n")
    status_dict["analytics"] = "Completed"
    print(f" Analytics result saved: {result}")
