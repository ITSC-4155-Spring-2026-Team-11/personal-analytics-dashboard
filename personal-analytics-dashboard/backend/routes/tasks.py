from fastapi import APIRouter

router = APIRouter()

# MVP in-memory storage (replace with DB in Milestone 2)
TASKS = []

@router.get("/")
def list_tasks():
    return {"tasks": TASKS}

@router.post("/")
def create_task(task: dict):
    # Minimal validation for MVP
    if "title" not in task or not task["title"].strip():
        return {"created": False, "error": "Task must include a non-empty title"}

    if "duration_minutes" not in task:
        task["duration_minutes"] = 30

    if "importance" not in task:
        task["importance"] = 3

    TASKS.append(task)
    return {"created": True, "task": task, "count": len(TASKS)}
