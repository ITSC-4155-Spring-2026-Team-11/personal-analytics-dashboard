def predict_stress(features: dict) -> float:
    """
    Placeholder stress score 0.0 - 1.0
    Later: replace with a trained model.
    """
    total_hours = float(features.get("total_hours", 0))
    return min(1.0, total_hours / 10.0)
