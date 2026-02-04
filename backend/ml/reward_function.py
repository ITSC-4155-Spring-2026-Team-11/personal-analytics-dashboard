def reward_from_feedback(stress_level: int) -> float:
    """
    Example reward mapping:
    - balanced (3) => +1.0
    - stressed (4-5) => negative
    - underwhelmed (1-2) => slightly negative
    """
    if stress_level == 3:
        return 1.0
    if stress_level >= 4:
        return -1.0
    return -0.3
