from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import (
    APP_BASE_URL,
    FRONTEND_BASE_URL,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI,
)
from backend.dependencies import get_current_user, get_db
from backend.models import IntegrationCredential, User
from backend.security import create_oauth_state_token, decode_oauth_state_token


router = APIRouter(prefix="/integrations", tags=["integrations"])


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _redirect_uri() -> str:
    if GOOGLE_OAUTH_REDIRECT_URI:
        return GOOGLE_OAUTH_REDIRECT_URI
    return f"{APP_BASE_URL.rstrip('/')}/integrations/google/callback"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_google_configured() -> None:
    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.",
        )


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    connected_at: Optional[str] = None
    scopes: Optional[str] = None


@router.get("")
def list_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    rows = (
        db.query(IntegrationCredential)
        .filter(IntegrationCredential.user_id == current_user.id)
        .all()
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            IntegrationStatus(
                provider=r.provider,
                connected=True,
                connected_at=r.created_at.isoformat() if r.created_at else None,
                scopes=r.scope,
            ).model_dump()
        )
    # Include known providers even if disconnected (for UI)
    known = {"google"}
    have = {r["provider"] for r in out}
    for p in sorted(known - have):
        out.append(IntegrationStatus(provider=p, connected=False).model_dump())
    return {"integrations": out}


@router.post("/google/disconnect")
def disconnect_google(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == current_user.id,
        IntegrationCredential.provider == "google",
    ).delete()
    db.commit()
    return {"disconnected": True}


@router.get("/google/authorize")
def google_authorize(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ensure_google_configured()

    state = create_oauth_state_token(int(current_user.id), provider="google", minutes_valid=10)
    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"authorization_url": url}


@router.get("/google/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    OAuth callback from Google. Exchanges code for tokens, saves them,
    then redirects back to the frontend Account settings page.
    """
    _ensure_google_configured()

    try:
        payload = decode_oauth_state_token(state)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if payload.get("provider") != "google":
        raise HTTPException(status_code=400, detail="Invalid OAuth provider")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user")

    data = {
        "code": code,
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": _redirect_uri(),
        "grant_type": "authorization_code",
    }

    try:
        resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to reach Google token endpoint")

    if not resp.ok:
        raise HTTPException(status_code=400, detail="Google token exchange failed")

    token = resp.json()
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Google token response missing access_token")

    expires_in = token.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)):
        expires_at = _utc_now() + timedelta(seconds=int(expires_in))

    # Upsert credentials
    row = (
        db.query(IntegrationCredential)
        .filter(IntegrationCredential.user_id == user.id, IntegrationCredential.provider == "google")
        .first()
    )
    if row is None:
        row = IntegrationCredential(
            user_id=user.id,
            provider="google",
            access_token=str(access_token),
            refresh_token=token.get("refresh_token"),
            token_type=token.get("token_type"),
            scope=token.get("scope"),
            expires_at=expires_at,
        )
        db.add(row)
    else:
        row.access_token = str(access_token)
        # Google may omit refresh_token on subsequent auths; keep existing unless provided.
        if token.get("refresh_token"):
            row.refresh_token = token.get("refresh_token")
        row.token_type = token.get("token_type")
        row.scope = token.get("scope")
        row.expires_at = expires_at

    db.commit()

    # Redirect back to frontend with a small success flag
    return RedirectResponse(url=f"{FRONTEND_BASE_URL}/account?google=connected")

