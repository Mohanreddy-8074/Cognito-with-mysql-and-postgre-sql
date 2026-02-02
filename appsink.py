import json
import requests
import os

# --- Configuration ---
API_KEY = "da2-4sygqzlqjrbuhnqt5qiqqbs7ui"
URL = "https://ofsb3xey35drzcvoo452azro4a.appsync-api.eu-north-1.amazonaws.com/event"

path = os.path.join(os.path.dirname(__file__), "data.json")

# 1. Load data
with open(path, "r") as f:
    data_content = json.load(f)

# 2. Format for AppSync Events
# Replace 'default/test' with your actual Namespace/Channel from the AWS Console
payload = {
    "channel": "sms/channel",  # 'sms' is the namespace, '/channel' is the channel
    "events": [
        json.dumps(data_content)  # Your event data
    ]
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# --- Execution ---
try:
    print(f"Publishing to: {URL}...")
    response = requests.post(URL, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("Success! Event published.")
        print("Response:", json.dumps(response.json(), indent=2))
    else:
        # If this still says 404, check if your endpoint requires /events (plural)
        print("Response:", response.text)

except Exception as e:
    print(f"Error: {e}")