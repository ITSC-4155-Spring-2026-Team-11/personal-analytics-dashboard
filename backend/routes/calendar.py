from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models import IntegrationCredential, Task, User, UserPreferences


router = APIRouter(prefix="/calendar", tags=["calendar"])


GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_rfc3339(s: str) -> datetime:
    # Google returns ISO with timezone offsets; sometimes ends in 'Z'
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _hhmm(dt: datetime) -> str:
    return f"{dt.hour:02d}:{dt.minute:02d}"


def _get_or_create_prefs(user: User, db: Session) -> UserPreferences:
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def _refresh_google_token(row: IntegrationCredential) -> None:
    if not row.refresh_token:
        raise HTTPException(status_code=401, detail="Google refresh token missing; reconnect Google Calendar.")

    from backend.config import GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET

    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured on the server.")

    data = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "refresh_token": row.refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to reach Google token endpoint")
    if not resp.ok:
        raise HTTPException(status_code=401, detail="Google token refresh failed; reconnect Google Calendar.")
    tok = resp.json()
    access_token = tok.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Google token refresh response missing access_token.")
    row.access_token = str(access_token)
    expires_in = tok.get("expires_in")
    if isinstance(expires_in, (int, float)):
        row.expires_at = _utc_now() + timedelta(seconds=int(expires_in))


def _get_google_access_token(db: Session, user_id: int) -> IntegrationCredential:
    row = (
        db.query(IntegrationCredential)
        .filter(IntegrationCredential.user_id == user_id, IntegrationCredential.provider == "google")
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Google Calendar is not connected.")

    if row.expires_at is not None and _ensure_utc(row.expires_at) <= _utc_now() + timedelta(seconds=30):
        _refresh_google_token(row)
        db.commit()
        db.refresh(row)

    return row


class SyncResult(BaseModel):
    imported: int
    updated: int
    skipped: int


@router.post("/google/sync", response_model=SyncResult)
def sync_google_calendar(
    start_date: Optional[str] = None,  # YYYY-MM-DD
    end_date: Optional[str] = None,    # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncResult:
    """
    Imports Google Calendar events into the user's Tasks as fixed-time items.
    """
    creds = _get_google_access_token(db, current_user.id)
    prefs = _get_or_create_prefs(current_user, db)

    # Default window: today -> +30 days
    today = datetime.now(timezone.utc).date()
    if start_date:
        try:
            start = datetime.fromisoformat(start_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date. Use YYYY-MM-DD.")
    else:
        start = today

    if end_date:
        try:
            end = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date. Use YYYY-MM-DD.")
    else:
        end = start + timedelta(days=30)

    # Google API expects RFC3339 timestamps
    time_min = datetime(start.year, start.month, start.day, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    time_max = datetime(end.year, end.month, end.day, 23, 59, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    headers = {"Authorization": f"Bearer {creds.access_token}"}
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 2500,
    }

    imported = 0
    updated = 0
    skipped = 0

    page_token: Optional[str] = None
    while True:
        if page_token:
            params["pageToken"] = page_token
        else:
            params.pop("pageToken", None)

        try:
            resp = requests.get(GOOGLE_EVENTS_URL, headers=headers, params=params, timeout=20)
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to reach Google Calendar API")

        if resp.status_code == 401:
            # Token might have expired early; force refresh once.
            _refresh_google_token(creds)
            db.commit()
            headers = {"Authorization": f"Bearer {creds.access_token}"}
            resp = requests.get(GOOGLE_EVENTS_URL, headers=headers, params=params, timeout=20)

        if not resp.ok:
            raise HTTPException(status_code=400, detail="Google Calendar API error")

        data = resp.json()
        items = data.get("items", []) or []

        for ev in items:
            if ev.get("status") == "cancelled":
                skipped += 1
                continue

            external_id = ev.get("id")
            if not external_id:
                skipped += 1
                continue

            summary = (ev.get("summary") or "Calendar event").strip()
            location = (ev.get("location") or None)

            start_obj = ev.get("start") or {}
            end_obj = ev.get("end") or {}

            # All-day events: start.date / end.date (end is exclusive)
            if "dateTime" in start_obj and "dateTime" in end_obj:
                start_dt = _parse_rfc3339(str(start_obj["dateTime"]))
                end_dt = _parse_rfc3339(str(end_obj["dateTime"]))
            elif "date" in start_obj and "date" in end_obj:
                # Represent all-day as the user's wake -> sleep window (better UX than 00:00-23:59).
                try:
                    day = datetime.fromisoformat(str(start_obj["date"])).date()
                except ValueError:
                    skipped += 1
                    continue
                wake_h, wake_m = map(int, (prefs.wake_time or "07:00").split(":"))
                sleep_h, sleep_m = map(int, (prefs.sleep_time or "23:00").split(":"))
                start_dt = datetime(day.year, day.month, day.day, wake_h, wake_m, tzinfo=timezone.utc)
                end_dt = datetime(day.year, day.month, day.day, sleep_h, sleep_m, tzinfo=timezone.utc)
            else:
                skipped += 1
                continue

            if end_dt <= start_dt:
                skipped += 1
                continue

            deadline = start_dt.date().isoformat()
            fixed_start = _hhmm(start_dt)
            fixed_end = _hhmm(end_dt)
            duration = int((end_dt - start_dt).total_seconds() // 60) or 30

            # Upsert into tasks
            existing = (
                db.query(Task)
                .filter(
                    Task.user_id == current_user.id,
                    Task.external_provider == "google",
                    Task.external_id == str(external_id),
                )
                .first()
            )

            if existing is None:
                t = Task(
                    user_id=current_user.id,
                    title=summary,
                    task_type="fixed",
                    deadline=deadline,
                    fixed_start=fixed_start,
                    fixed_end=fixed_end,
                    duration_minutes=duration,
                    location=location,
                    energy_level="medium",
                    preferred_time="none",
                    recurrence="none",
                    source="google_calendar",
                    external_provider="google",
                    external_id=str(external_id),
                    imported_at=_utc_now(),
                )
                db.add(t)
                imported += 1
            else:
                # Keep user completion; if they completed it, don't stomp fields.
                if bool(existing.completed):
                    skipped += 1
                    continue
                existing.title = summary
                existing.deadline = deadline
                existing.task_type = "fixed"
                existing.fixed_start = fixed_start
                existing.fixed_end = fixed_end
                existing.duration_minutes = duration
                existing.location = location
                existing.source = "google_calendar"
                existing.external_provider = "google"
                existing.external_id = str(external_id)
                existing.imported_at = _utc_now()
                updated += 1

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    db.commit()
    return SyncResult(imported=imported, updated=updated, skipped=skipped)

