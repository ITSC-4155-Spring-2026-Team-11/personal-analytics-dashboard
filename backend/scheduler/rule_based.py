from scheduler.constraints import apply_constraints
from scheduler.priority_engine import sort_by_priority

def build_schedule(tasks, appointments, day_start="09:00", day_end="17:00"):
    """
    MVP Rule-based scheduler:
    1) Sort tasks by priority (importance-based for now)
    2) Fill time starting at day_start
    3) Apply constraints (appointments, bounds)
    """

    sorted_tasks = sort_by_priority(tasks)

    # naive time-fill (placeholder)
    current_time = day_start
    schedule = []

    for t in sorted_tasks:
        schedule.append({
            "time": current_time,
            "task": t["title"],
            "minutes": t.get("duration_minutes", 30)
        })

        # NOTE: time increment is not implemented in MVP
        # later: convert HH:MM -> minutes, add duration, convert back

    schedule = apply_constraints(schedule, appointments, day_start, day_end)
    return schedule
