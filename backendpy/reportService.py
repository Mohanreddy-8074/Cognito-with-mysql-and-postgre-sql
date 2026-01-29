import time

def generate_report(user_email, status_dict):
    status_dict["report"] = "Running"
    print(f"Generating report for {user_email}...")
    time.sleep(5)  # simulate heavy processing
    filename = f"{user_email}_report.txt"
    with open(filename, "w") as f:
        f.write(f"Report for {user_email} generated successfully!")
    status_dict["report"] = "Completed"
    print(f" Report saved: {filename}")
