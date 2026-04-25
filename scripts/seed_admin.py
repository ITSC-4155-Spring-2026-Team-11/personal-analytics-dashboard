"""
Seed script: creates an admin user (admin@admin.com / Test1234) and populates
two weeks of tasks — one past week (mostly completed) and one upcoming week.

Run from the project root:
    python scripts/seed_admin.py
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure the project root is on sys.path so backend imports work.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.database import SessionLocal, engine, Base
from backend.models import Task, User
from backend.security import hash_password

# ── Constants ────────────────────────────────────────────────────────────────

ADMIN_NAME     = "admin"
ADMIN_EMAIL    = "admin@admin.com"
ADMIN_PASSWORD = "Test1234"

TODAY = datetime.now(timezone.utc).date()
WEEK_AGO    = TODAY - timedelta(days=7)
WEEK_AHEAD  = TODAY + timedelta(days=6)


def _d(offset_days: int) -> str:
    """Return YYYY-MM-DD for today + offset_days."""
    return (TODAY + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _dt(offset_days: int) -> datetime:
    return datetime.combine(
        TODAY + timedelta(days=offset_days),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )


# ── Task definitions ─────────────────────────────────────────────────────────
# Each dict maps to Task fields.  'day_offset' < 0 = past, >= 0 = future/today.

TASK_TEMPLATES: list[dict] = [
    # ── Past week (days -7 to -1) ─────────────────────────────────────────────
    {
        "title": "Morning run",
        "category": "Exercise", "task_type": "fixed",
        "fixed_start": "07:00", "fixed_end": "07:45",
        "duration_minutes": 45, "importance": 4, "energy_level": "high",
        "preferred_time": "morning", "day_offset": -7,
        "completed": True, "actual_duration": 43,
    },
    {
        "title": "Team standup",
        "category": "Work", "task_type": "fixed",
        "fixed_start": "09:00", "fixed_end": "09:30",
        "duration_minutes": 30, "importance": 5, "energy_level": "medium",
        "preferred_time": "morning", "day_offset": -7,
        "completed": True, "actual_duration": 28,
    },
    {
        "title": "Read chapter 3 — Algorithms book",
        "category": "Study", "task_type": "semi",
        "duration_minutes": 60, "importance": 3, "energy_level": "high",
        "preferred_time": "afternoon", "day_offset": -7,
        "completed": True, "actual_duration": 65,
    },
    {
        "title": "Grocery shopping",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 45, "importance": 2, "energy_level": "low",
        "preferred_time": "none", "day_offset": -6,
        "completed": True, "actual_duration": 50,
    },
    {
        "title": "Sprint planning",
        "category": "Work", "task_type": "fixed",
        "fixed_start": "10:00", "fixed_end": "11:00",
        "duration_minutes": 60, "importance": 5, "energy_level": "high",
        "preferred_time": "morning", "day_offset": -6,
        "completed": True, "actual_duration": 62,
    },
    {
        "title": "Gym — chest & triceps",
        "category": "Exercise", "task_type": "semi",
        "duration_minutes": 75, "importance": 4, "energy_level": "high",
        "preferred_time": "evening", "day_offset": -6,
        "completed": True, "actual_duration": 80,
    },
    {
        "title": "Review pull requests",
        "category": "Work", "task_type": "flexible",
        "duration_minutes": 45, "importance": 4, "energy_level": "medium",
        "preferred_time": "afternoon", "day_offset": -5,
        "completed": True, "actual_duration": 40,
    },
    {
        "title": "Watch lecture — Data Structures",
        "category": "Study", "task_type": "semi",
        "duration_minutes": 90, "importance": 4, "energy_level": "high",
        "preferred_time": "evening", "day_offset": -5,
        "completed": True, "actual_duration": 95,
    },
    {
        "title": "Yoga session",
        "category": "Exercise", "task_type": "flexible",
        "duration_minutes": 30, "importance": 3, "energy_level": "low",
        "preferred_time": "morning", "day_offset": -4,
        "completed": True, "actual_duration": 30,
    },
    {
        "title": "Write unit tests for auth module",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 120, "importance": 5, "energy_level": "high",
        "preferred_time": "morning", "day_offset": -4,
        "completed": True, "actual_duration": 135,
    },
    {
        "title": "Nap / rest",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 30, "importance": 1, "energy_level": "low",
        "preferred_time": "afternoon", "day_offset": -4,
        "completed": True, "actual_duration": 25,
    },
    {
        "title": "1-on-1 with manager",
        "category": "Work", "task_type": "fixed",
        "fixed_start": "14:00", "fixed_end": "14:30",
        "duration_minutes": 30, "importance": 4, "energy_level": "medium",
        "preferred_time": "afternoon", "day_offset": -3,
        "completed": True, "actual_duration": 30,
    },
    {
        "title": "Practice LeetCode problems",
        "category": "Study", "task_type": "flexible",
        "duration_minutes": 60, "importance": 3, "energy_level": "high",
        "preferred_time": "evening", "day_offset": -3,
        "completed": True, "actual_duration": 70,
    },
    {
        "title": "Evening walk",
        "category": "Exercise", "task_type": "flexible",
        "duration_minutes": 30, "importance": 2, "energy_level": "low",
        "preferred_time": "evening", "day_offset": -2,
        "completed": True, "actual_duration": 35,
    },
    {
        "title": "Refactor database layer",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 90, "importance": 4, "energy_level": "high",
        "preferred_time": "morning", "day_offset": -2,
        "completed": False,
    },
    {
        "title": "Read research paper",
        "category": "Study", "task_type": "flexible",
        "duration_minutes": 45, "importance": 2, "energy_level": "medium",
        "preferred_time": "afternoon", "day_offset": -1,
        "completed": True, "actual_duration": 50,
    },
    {
        "title": "Weekly review & journaling",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 30, "importance": 3, "energy_level": "low",
        "preferred_time": "evening", "day_offset": -1,
        "completed": True, "actual_duration": 28,
    },

    # ── Today (day 0) ─────────────────────────────────────────────────────────
    {
        "title": "Morning run",
        "category": "Exercise", "task_type": "fixed",
        "fixed_start": "07:00", "fixed_end": "07:45",
        "duration_minutes": 45, "importance": 4, "energy_level": "high",
        "preferred_time": "morning", "day_offset": 0,
        "completed": False,
    },
    {
        "title": "Daily standup",
        "category": "Work", "task_type": "fixed",
        "fixed_start": "09:00", "fixed_end": "09:30",
        "duration_minutes": 30, "importance": 5, "energy_level": "medium",
        "preferred_time": "morning", "day_offset": 0,
        "completed": False,
    },
    {
        "title": "Work on analytics dashboard feature",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 120, "importance": 5, "energy_level": "high",
        "preferred_time": "morning", "day_offset": 0,
        "completed": False,
    },
    {
        "title": "Study — OS concepts chapter 5",
        "category": "Study", "task_type": "flexible",
        "duration_minutes": 60, "importance": 3, "energy_level": "high",
        "preferred_time": "afternoon", "day_offset": 0,
        "completed": False,
    },

    # ── Upcoming week (days +1 to +6) ─────────────────────────────────────────
    {
        "title": "Gym — back & biceps",
        "category": "Exercise", "task_type": "semi",
        "duration_minutes": 75, "importance": 4, "energy_level": "high",
        "preferred_time": "evening", "day_offset": 1,
        "completed": False,
    },
    {
        "title": "Write project report draft",
        "category": "Study", "task_type": "semi",
        "duration_minutes": 90, "importance": 4, "energy_level": "high",
        "preferred_time": "afternoon", "day_offset": 1,
        "completed": False,
    },
    {
        "title": "Deploy hotfix to staging",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 60, "importance": 5, "energy_level": "high",
        "preferred_time": "morning", "day_offset": 2,
        "completed": False,
    },
    {
        "title": "Yoga session",
        "category": "Exercise", "task_type": "flexible",
        "duration_minutes": 30, "importance": 3, "energy_level": "low",
        "preferred_time": "morning", "day_offset": 2,
        "completed": False,
    },
    {
        "title": "Catch up on Slack / emails",
        "category": "Work", "task_type": "flexible",
        "duration_minutes": 30, "importance": 2, "energy_level": "low",
        "preferred_time": "morning", "day_offset": 3,
        "completed": False,
    },
    {
        "title": "Complete problem set 4",
        "category": "Study", "task_type": "semi",
        "duration_minutes": 120, "importance": 5, "energy_level": "high",
        "preferred_time": "afternoon", "day_offset": 3,
        "completed": False,
    },
    {
        "title": "Evening walk",
        "category": "Exercise", "task_type": "flexible",
        "duration_minutes": 30, "importance": 2, "energy_level": "low",
        "preferred_time": "evening", "day_offset": 3,
        "completed": False,
    },
    {
        "title": "Code review — teammate's PR",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 45, "importance": 4, "energy_level": "medium",
        "preferred_time": "morning", "day_offset": 4,
        "completed": False,
    },
    {
        "title": "Meal prep for the week",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 60, "importance": 3, "energy_level": "low",
        "preferred_time": "afternoon", "day_offset": 4,
        "completed": False,
    },
    {
        "title": "Gym — legs",
        "category": "Exercise", "task_type": "semi",
        "duration_minutes": 75, "importance": 4, "energy_level": "high",
        "preferred_time": "evening", "day_offset": 5,
        "completed": False,
    },
    {
        "title": "Prepare presentation slides",
        "category": "Work", "task_type": "semi",
        "duration_minutes": 90, "importance": 5, "energy_level": "high",
        "preferred_time": "afternoon", "day_offset": 5,
        "completed": False,
    },
    {
        "title": "Read for fun — fiction",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 45, "importance": 1, "energy_level": "low",
        "preferred_time": "evening", "day_offset": 5,
        "completed": False,
    },
    {
        "title": "Weekly review & planning",
        "category": "Rest", "task_type": "flexible",
        "duration_minutes": 30, "importance": 3, "energy_level": "low",
        "preferred_time": "evening", "day_offset": 6,
        "completed": False,
    },
    {
        "title": "Submit project deliverable",
        "category": "Study", "task_type": "semi",
        "duration_minutes": 30, "importance": 5, "energy_level": "medium",
        "preferred_time": "morning", "day_offset": 6,
        "completed": False,
    },
]


def _make_task(user_id: int, t: dict) -> Task:
    offset  = t["day_offset"]
    date_str = _d(offset)
    completed = t.get("completed", False)
    completed_at = _dt(offset) if completed else None

    return Task(
        user_id              = user_id,
        title                = t["title"],
        category             = t.get("category", "Work"),
        task_type            = t.get("task_type", "flexible"),
        duration_minutes     = t.get("duration_minutes", 30),
        importance           = t.get("importance", 3),
        energy_level         = t.get("energy_level", "medium"),
        preferred_time       = t.get("preferred_time", "none"),
        fixed_start          = t.get("fixed_start"),
        fixed_end            = t.get("fixed_end"),
        deadline             = date_str,
        last_scheduled_date  = date_str,
        completed            = completed,
        completed_at         = completed_at,
        actual_duration      = t.get("actual_duration"),
        actual_time_of_day   = t.get("preferred_time") if completed else None,
    )


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # ── Create or fetch admin user ─────────────────────────────────────────
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user is None:
            user = User(
                name          = ADMIN_NAME,
                email         = ADMIN_EMAIL,
                password_hash = hash_password(ADMIN_PASSWORD),
                is_verified   = True,
                is_active     = True,
            )
            db.add(user)
            db.flush()
            print(f"Created user: {ADMIN_EMAIL}")
        else:
            user.is_verified = True
            db.flush()
            print(f"User already exists: {ADMIN_EMAIL} (verified=True ensured)")

        user_id = int(user.id)

        # ── Remove existing tasks for this user (idempotent re-run) ───────────
        existing = db.query(Task).filter(Task.user_id == user_id).count()
        if existing:
            db.query(Task).filter(Task.user_id == user_id).delete()
            print(f"Cleared {existing} existing tasks for {ADMIN_EMAIL}")

        # ── Insert tasks ──────────────────────────────────────────────────────
        tasks = [_make_task(user_id, t) for t in TASK_TEMPLATES]
        db.add_all(tasks)
        db.commit()

        total      = len(tasks)
        completed  = sum(1 for t in TASK_TEMPLATES if t.get("completed"))
        categories = {}
        for t in TASK_TEMPLATES:
            categories[t.get("category", "Work")] = categories.get(t.get("category", "Work"), 0) + 1

        print(f"\nSeeded {total} tasks for '{ADMIN_NAME}' ({ADMIN_EMAIL})")
        print(f"  Completed : {completed}")
        print(f"  Pending   : {total - completed}")
        print(f"  By category: {categories}")
        print(f"\nLogin credentials:")
        print(f"  Email    : {ADMIN_EMAIL}")
        print(f"  Password : {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
