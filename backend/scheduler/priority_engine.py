def sort_by_priority(tasks):
    """
    MVP: Sort descending importance.
    Later: combine importance + deadline urgency + user preferences.
    """
    def score(task):
        return int(task.get("importance", 3))

    return sorted(tasks, key=score, reverse=True)
