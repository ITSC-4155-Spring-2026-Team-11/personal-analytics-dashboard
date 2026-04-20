"""
analytics.py
------------
Analytics endpoints.

GET /analytics/daily?date=YYYY-MM-DD
    Returns all tasks relevant to a given date plus a category breakdown.
    "Relevant" = completed that day (via completed_at) OR deadline == date.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.models import Task, User
from backend.dependencies import get_db, get_current_user

router = APIRouter()


def _format_duration(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m" if m else f"{h}h"


@router.get("/daily")
def daily_summary(
    date         : str     = Query(..., description="Date in YYYY-MM-DD format"),
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Returns tasks relevant to `date`:
      - Completed tasks where completed_at date == date
      - Any task whose deadline == date (completed or not)

    Response includes:
      - tasks list with title, duration_minutes, category, completed
      - total_minutes across all returned tasks
      - total_formatted  e.g. "6h 30m"
      - by_category dict  e.g. { "Work": 120, "Study": 90 }
    """
    all_tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .all()
    )

    seen_ids: set[int] = set()
    result: list[Task] = []

    for task in all_tasks:
        # Include if deadline matches
        if task.deadline == date:
            seen_ids.add(task.id)
            result.append(task)
            continue
        # Include if completed on this date
        if task.completed and task.completed_at:
            completed_date = task.completed_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
            if completed_date == date and task.id not in seen_ids:
                seen_ids.add(task.id)
                result.append(task)

    # Build response
    total_minutes = sum(t.duration_minutes for t in result)

    by_category: dict[str, int] = defaultdict(int)
    for t in result:
        by_category[t.category] += t.duration_minutes

    serialized = [
        {
            "id"              : t.id,
            "title"           : t.title,
            "category"        : t.category,
            "duration_minutes": t.duration_minutes,
            "duration_label"  : _format_duration(t.duration_minutes),
            "completed"       : t.completed,
            "task_type"       : t.task_type,
            "fixed_start"     : t.fixed_start,
            "fixed_end"       : t.fixed_end,
            "importance"      : t.importance,
        }
        for t in result
    ]

    return {
        "date"           : date,
        "tasks"          : serialized,
        "total_minutes"  : total_minutes,
        "total_formatted": _format_duration(total_minutes),
        "by_category"    : dict(by_category),
        "task_count"     : len(result),
    }