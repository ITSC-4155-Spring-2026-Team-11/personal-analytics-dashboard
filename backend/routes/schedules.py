from fastapi import APIRouter
from datetime import datetime
from backend.scheduler.rule_based import build_schedule

router = APIRouter()

# Simple sample tasks for MVP (later use DB)
DEFAULT_TASKS = [
    {"title": "Workout", "duration_minutes": 45, "importance": 4},
    {"title": "Study", "duration_minutes": 120, "importance": 5},
    {"title": "Lunch", "duration_minutes": 45, "importance": 2},
]

@router.get("/today")
def get_todays_schedule():
    today = datetime.now().strftime("%Y-%m-%d")

    # Appointments placeholder (future: calendar integration)
    appointments = [
        {"start": "15:00", "end": "15:30", "title": "Appointment"}
    ]

    schedule_items = build_schedule(DEFAULT_TASKS, appointments)

    return {"date": today, "items": schedule_items}
