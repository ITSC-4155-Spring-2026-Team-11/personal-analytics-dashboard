from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from backend.database import SessionLocal
from backend.models import Task, User
from backend.dependencies import get_db, get_current_user

router = APIRouter()


# ── Request schemas ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title:            str
    duration_minutes: Optional[int] = 30
    deadline:         Optional[str] = None
    importance:       Optional[int] = 3
    task_type:        Optional[str] = "flexible"
    fixed_start:      Optional[str] = None
    fixed_end:        Optional[str] = None
    location:         Optional[str] = None
    energy_level:     Optional[str] = "moderate"
    preferred_time:   Optional[str] = "none"
    recurrence:       Optional[str] = "once"
    recurrence_days:  Optional[str] = None


class TaskUpdate(BaseModel):
    title:            Optional[str] = None
    duration_minutes: Optional[int] = None
    deadline:         Optional[str] = None
    importance:       Optional[int] = None
    task_type:        Optional[str] = None
    fixed_start:      Optional[str] = None
    fixed_end:        Optional[str] = None
    location:         Optional[str] = None
    energy_level:     Optional[str] = None
    preferred_time:   Optional[str] = None
    recurrence:       Optional[str] = None
    recurrence_days:  Optional[str] = None


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/")
def list_tasks(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return {"tasks": tasks}


@router.post("/", status_code=201)
def create_task(
    body:         TaskCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    if not body.title.strip():
        raise HTTPException(status_code=422, detail="Task title cannot be empty")

    task = Task(
        user_id          = current_user.id,
        title            = body.title.strip(),
        duration_minutes = body.duration_minutes,
        deadline         = body.deadline,
        importance       = body.importance,
        task_type        = body.task_type,
        fixed_start      = body.fixed_start,
        fixed_end        = body.fixed_end,
        location         = body.location,
        energy_level     = body.energy_level,
        preferred_time   = body.preferred_time,
        recurrence       = body.recurrence,
        recurrence_days  = body.recurrence_days,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"created": True, "task": task}


@router.patch("/{task_id}")
def update_task(
    task_id:      int,
    body:         TaskUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id      == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        if not body.title.strip():
            raise HTTPException(status_code=422, detail="Task title cannot be empty")
        task.title = body.title.strip()
    if body.duration_minutes is not None:
        task.duration_minutes = body.duration_minutes
    if body.deadline is not None:
        task.deadline = body.deadline if body.deadline else None
    if body.importance is not None:
        if not 1 <= body.importance <= 5:
            raise HTTPException(status_code=422, detail="Importance must be between 1 and 5")
        task.importance = body.importance
    if body.task_type is not None:
        task.task_type = body.task_type
    if body.fixed_start is not None:
        task.fixed_start = body.fixed_start if body.fixed_start else None
    if body.fixed_end is not None:
        task.fixed_end = body.fixed_end if body.fixed_end else None
    if body.location is not None:
        task.location = body.location if body.location else None
    if body.energy_level is not None:
        task.energy_level = body.energy_level
    if body.preferred_time is not None:
        task.preferred_time = body.preferred_time
    if body.recurrence is not None:
        task.recurrence = body.recurrence
    if body.recurrence_days is not None:
        task.recurrence_days = body.recurrence_days if body.recurrence_days else None

    db.commit()
    db.refresh(task)
    return {"updated": True, "task": task}


@router.patch("/{task_id}/complete")
def toggle_complete(
    task_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id      == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = not task.completed
    task.completed_at = datetime.now(timezone.utc) if task.completed else None

    db.commit()
    db.refresh(task)
    return {"updated": True, "completed": task.completed, "task": task}


@router.delete("/{task_id}")
def delete_task(
    task_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id      == task_id,
        Task.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"deleted": True}