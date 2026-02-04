def build_state(schedule_items, feedback_history):
    """
    Placeholder:
    Convert schedule + feedback into a simple state representation.
    """
    num_tasks = len(schedule_items)
    last_stress = feedback_history[-1]["stress_level"] if feedback_history else 3
    return {"num_tasks": num_tasks, "last_stress": last_stress}
