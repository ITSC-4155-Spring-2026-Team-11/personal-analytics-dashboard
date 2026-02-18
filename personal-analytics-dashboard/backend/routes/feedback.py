from fastapi import APIRouter

router = APIRouter()

# MVP in-memory feedback log (replace with DB)
FEEDBACK_LOG = []

@router.post("/")
def submit_feedback(payload: dict):
    # Expecting: { "date": "YYYY-MM-DD", "stress_level": 1-5, "notes": "..." }
    if "date" not in payload or "stress_level" not in payload:
        return {"saved": False, "error": "Payload must include date and stress_level"}

    FEEDBACK_LOG.append(payload)
    return {"saved": True, "payload": payload, "count": len(FEEDBACK_LOG)}
