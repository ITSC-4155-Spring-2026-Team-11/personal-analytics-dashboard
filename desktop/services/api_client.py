import requests

API_BASE = "http://127.0.0.1:8000"

def get_today_schedule():
    response = requests.get(f"{API_BASE}/schedules/today")
    response.raise_for_status()
    return response.json()

def submit_feedback(payload: dict):
    response = requests.post(f"{API_BASE}/feedback", json=payload)
    response.raise_for_status()
    return response.json()
