"""
Unit tests for the Google Calendar integration.

Covers:
  integrations.py  — GET /integrations (list), POST /integrations/google/disconnect,
                     GET /integrations/google/authorize,
                     GET /integrations/google/callback
  calendar.py      — POST /calendar/google/sync  (import, update, skip, pagination,
                     token refresh, network errors, date-parsing edge cases)
"""

from __future__ import annotations

import bootstrap_sys_path  # noqa: F401

import base64
import json as _json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.models import IntegrationCredential
from backend.security import create_oauth_state_token
from backend.tests.helpers import auth_headers, login_form, register_verified_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, *, email="cal@example.com", password="CalUser1", name="Cal User"):
    register_verified_user(client, email=email, password=password, name=name)
    r = login_form(client, email, password)
    assert r.status_code == 200
    return r.json()["access_token"]


def _get_user_id(token: str) -> int:
    """Decode the user ID from the JWT sub claim without a network call."""
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
    return int(payload["sub"])


def _fake_ok_response(body: dict, status: int = 200) -> MagicMock:
    m = MagicMock()
    m.ok = status < 400
    m.status_code = status
    m.json.return_value = body
    return m


def _seed_google_creds(
    db_session,
    user_id: int,
    *,
    access_token: str = "access-tok",
    refresh_token: str | None = "refresh-tok",
    expires_at: datetime | None = None,
) -> IntegrationCredential:
    """Insert a Google IntegrationCredential directly via session."""
    row = IntegrationCredential(
        user_id=user_id,
        provider="google",
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at or datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def token(client):
    return _register_and_login(client)


# ===========================================================================
# GET /integrations  — list
# ===========================================================================

class TestListIntegrations:
    def test_unauthenticated_returns_401(self, client):
        r = client.get("/integrations")
        assert r.status_code == 401

    def test_no_integrations_returns_google_disconnected(self, client, token):
        r = client.get("/integrations", headers=auth_headers(token))
        assert r.status_code == 200
        integrations = r.json()["integrations"]
        google = next(i for i in integrations if i["provider"] == "google")
        assert google["connected"] is False

    def test_connected_integration_shows_as_connected(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        r = client.get("/integrations", headers=auth_headers(token))
        assert r.status_code == 200
        google = next(i for i in r.json()["integrations"] if i["provider"] == "google")
        assert google["connected"] is True


# ===========================================================================
# POST /integrations/google/disconnect
# ===========================================================================

class TestDisconnectGoogle:
    def test_unauthenticated_returns_401(self, client):
        r = client.post("/integrations/google/disconnect")
        assert r.status_code == 401

    def test_disconnect_when_not_connected_is_idempotent(self, client, token):
        r = client.post("/integrations/google/disconnect", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["disconnected"] is True

    def test_disconnect_removes_credentials(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)

        r = client.post("/integrations/google/disconnect", headers=auth_headers(token))
        assert r.status_code == 200

        r2 = client.get("/integrations", headers=auth_headers(token))
        google = next(i for i in r2.json()["integrations"] if i["provider"] == "google")
        assert google["connected"] is False


# ===========================================================================
# GET /integrations/google/authorize
# ===========================================================================

class TestGoogleAuthorize:
    def test_unauthenticated_returns_401(self, client):
        r = client.get("/integrations/google/authorize")
        assert r.status_code == 401

    def test_returns_500_when_oauth_not_configured(self, client, token):
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", ""), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", ""):
            r = client.get("/integrations/google/authorize", headers=auth_headers(token))
        assert r.status_code == 500

    def test_returns_authorization_url_when_configured(self, client, token):
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "fake-client-id"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "fake-secret"):
            r = client.get("/integrations/google/authorize", headers=auth_headers(token))
        assert r.status_code == 200
        url = r.json()["authorization_url"]
        assert "accounts.google.com" in url
        assert "fake-client-id" in url
        assert "calendar.readonly" in url


# ===========================================================================
# GET /integrations/google/callback
# ===========================================================================

class TestGoogleCallback:
    """Follow-the-OAuth-code flow with mocked requests.post."""

    def _valid_state(self, user_id: int) -> str:
        return create_oauth_state_token(user_id, provider="google", minutes_valid=5)

    def test_invalid_state_returns_400(self, client):
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "csec"):
            r = client.get(
                "/integrations/google/callback",
                params={"code": "authcode", "state": "not-a-real-jwt"},
                follow_redirects=False,
            )
        assert r.status_code == 400

    def test_network_error_returns_502(self, client, token):
        uid = _get_user_id(token)
        state = self._valid_state(uid)
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch("backend.routes.integrations.requests.post", side_effect=ConnectionError):
            r = client.get(
                "/integrations/google/callback",
                params={"code": "authcode", "state": state},
                follow_redirects=False,
            )
        assert r.status_code == 502

    def test_bad_token_response_returns_400(self, client, token):
        uid = _get_user_id(token)
        state = self._valid_state(uid)
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch(
                "backend.routes.integrations.requests.post",
                return_value=_fake_ok_response({"error": "invalid_grant"}, status=400),
             ):
            r = client.get(
                "/integrations/google/callback",
                params={"code": "authcode", "state": state},
                follow_redirects=False,
            )
        assert r.status_code == 400

    def test_successful_callback_saves_credentials_and_redirects(self, client, token, db_session):
        uid = _get_user_id(token)
        state = self._valid_state(uid)
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch(
                "backend.routes.integrations.requests.post",
                return_value=_fake_ok_response({
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "https://www.googleapis.com/auth/calendar.readonly",
                }),
             ):
            r = client.get(
                "/integrations/google/callback",
                params={"code": "authcode", "state": state},
                follow_redirects=False,
            )
        assert r.status_code in (301, 302, 307, 308)
        row = (
            db_session.query(IntegrationCredential)
            .filter_by(user_id=uid, provider="google")
            .first()
        )
        assert row is not None
        assert row.access_token == "new-access"
        assert row.refresh_token == "new-refresh"

    def test_callback_upserts_existing_credential(self, client, token, db_session):
        """Second connect should update the existing row, not create a duplicate."""
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid, access_token="old-access")
        state = self._valid_state(uid)
        with patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.routes.integrations.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch(
                "backend.routes.integrations.requests.post",
                return_value=_fake_ok_response({"access_token": "updated-access", "expires_in": 3600}),
             ):
            r = client.get(
                "/integrations/google/callback",
                params={"code": "authcode", "state": state},
                follow_redirects=False,
            )
        assert r.status_code in (301, 302, 307, 308)
        rows = (
            db_session.query(IntegrationCredential)
            .filter_by(user_id=uid, provider="google")
            .all()
        )
        assert len(rows) == 1
        db_session.refresh(rows[0])
        assert rows[0].access_token == "updated-access"


# ===========================================================================
# POST /calendar/google/sync
# ===========================================================================

def _google_event(
    event_id: str = "evt1",
    summary: str = "Test Event",
    start: str = "2030-06-01T09:00:00Z",
    end: str = "2030-06-01T10:00:00Z",
    status: str = "confirmed",
    location: str | None = None,
) -> dict:
    ev: dict = {
        "id": event_id,
        "summary": summary,
        "status": status,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    if location:
        ev["location"] = location
    return ev


class TestSyncGoogleCalendar:
    def test_unauthenticated_returns_401(self, client):
        r = client.post("/calendar/google/sync")
        assert r.status_code == 401

    def test_no_credentials_returns_404(self, client, token):
        r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 404
        assert "not connected" in r.json()["detail"].lower()

    def test_network_error_on_events_fetch_returns_502(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        with patch("backend.routes.calendar.requests.get", side_effect=ConnectionError):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 502

    def test_google_api_error_returns_400(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        with patch(
            "backend.routes.calendar.requests.get",
            return_value=_fake_ok_response({"error": "forbidden"}, status=403),
        ):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 400

    def test_invalid_start_date_returns_400(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        r = client.post(
            "/calendar/google/sync",
            params={"start_date": "not-a-date"},
            headers=auth_headers(token),
        )
        assert r.status_code == 400

    def test_invalid_end_date_returns_400(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        r = client.post(
            "/calendar/google/sync",
            params={"end_date": "nope"},
            headers=auth_headers(token),
        )
        assert r.status_code == 400

    def test_imports_new_event(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event_page = {"items": [_google_event()], "nextPageToken": None}
        with patch(
            "backend.routes.calendar.requests.get",
            return_value=_fake_ok_response(event_page),
        ):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        body = r.json()
        assert body["imported"] == 1
        assert body["updated"] == 0
        assert body["skipped"] == 0

    def test_updates_existing_event(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        page1 = {"items": [_google_event(event_id="ev99", summary="First Title")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(page1)):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["imported"] == 1

        page2 = {"items": [_google_event(event_id="ev99", summary="Updated Title")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(page2)):
            r2 = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r2.status_code == 200
        assert r2.json()["updated"] == 1
        assert r2.json()["imported"] == 0

    def test_skips_cancelled_event(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event_page = {"items": [_google_event(status="cancelled")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(event_page)):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["skipped"] == 1
        assert r.json()["imported"] == 0

    def test_skips_event_with_no_id(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event = {
            "summary": "Mystery",
            "status": "confirmed",
            "start": {"dateTime": "2030-06-01T10:00:00Z"},
            "end": {"dateTime": "2030-06-01T11:00:00Z"},
        }
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response({"items": [event]})):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["skipped"] == 1

    def test_skips_event_with_no_time_fields(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event = {"id": "nope", "summary": "No time", "status": "confirmed", "start": {}, "end": {}}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response({"items": [event]})):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["skipped"] == 1

    def test_skips_completed_task_on_update(self, client, token, db_session):
        """If the task was already completed locally it should not be overwritten."""
        from backend.models import Task
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        page1 = {"items": [_google_event(event_id="done-ev")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(page1)):
            client.post("/calendar/google/sync", headers=auth_headers(token))

        task = db_session.query(Task).filter_by(user_id=uid, external_id="done-ev").first()
        assert task is not None
        task.completed = True
        db_session.commit()

        page2 = {"items": [_google_event(event_id="done-ev", summary="Renamed")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(page2)):
            r2 = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r2.json()["skipped"] == 1
        assert r2.json()["updated"] == 0

    def test_imports_all_day_event(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        all_day_event = {
            "id": "allday1",
            "summary": "All Day",
            "status": "confirmed",
            "start": {"date": "2030-07-04"},
            "end": {"date": "2030-07-05"},
        }
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response({"items": [all_day_event]})):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_skips_all_day_event_with_bad_date(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event = {
            "id": "bad-date",
            "summary": "Bad Date",
            "status": "confirmed",
            "start": {"date": "not-a-date"},
            "end": {"date": "not-a-date"},
        }
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response({"items": [event]})):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["skipped"] == 1

    def test_event_location_is_saved(self, client, token, db_session):
        from backend.models import Task
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        event_page = {"items": [_google_event(event_id="loc-ev", location="123 Main St")]}
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response(event_page)):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["imported"] == 1
        task = db_session.query(Task).filter_by(user_id=uid, external_id="loc-ev").first()
        assert task is not None
        assert task.location == "123 Main St"

    def test_empty_item_list_returns_zero_counts(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        with patch("backend.routes.calendar.requests.get", return_value=_fake_ok_response({"items": []})):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json() == {"imported": 0, "updated": 0, "skipped": 0}

    def test_pagination_fetches_all_pages(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        page1 = {"items": [_google_event("p1")], "nextPageToken": "tok2"}
        page2 = {"items": [_google_event("p2")]}
        responses = iter([_fake_ok_response(page1), _fake_ok_response(page2)])
        with patch("backend.routes.calendar.requests.get", side_effect=lambda *a, **kw: next(responses)):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.json()["imported"] == 2

    def test_custom_date_range_is_accepted(self, client, token, db_session):
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        with patch(
            "backend.routes.calendar.requests.get",
            return_value=_fake_ok_response({"items": []}),
        ) as mock_get:
            r = client.post(
                "/calendar/google/sync",
                params={"start_date": "2030-01-01", "end_date": "2030-01-31"},
                headers=auth_headers(token),
            )
        assert r.status_code == 200
        call_kwargs = mock_get.call_args[1]
        assert "2030-01-01T00:00:00Z" in call_kwargs["params"]["timeMin"]
        assert "2030-01-31T23:59:00Z" in call_kwargs["params"]["timeMax"]


# ===========================================================================
# Token refresh paths
# ===========================================================================

class TestTokenRefresh:
    def test_expired_token_triggers_refresh_before_sync(self, client, token, db_session):
        """A credential whose expires_at is in the past triggers a proactive refresh."""
        uid = _get_user_id(token)
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _seed_google_creds(
            db_session, uid,
            access_token="expired-tok",
            refresh_token="good-refresh",
            expires_at=expired_at,
        )
        refresh_resp = _fake_ok_response({"access_token": "fresh-tok", "expires_in": 3600})
        events_resp = _fake_ok_response({"items": [_google_event()]})
        with patch("backend.config.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.config.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch("backend.routes.calendar.requests.post", return_value=refresh_resp), \
             patch("backend.routes.calendar.requests.get", return_value=events_resp):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["imported"] == 1

    def test_refresh_with_no_refresh_token_returns_401(self, client, token, db_session):
        uid = _get_user_id(token)
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _seed_google_creds(
            db_session, uid,
            access_token="expired-tok",
            refresh_token=None,
            expires_at=expired_at,
        )
        r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 401

    def test_refresh_network_error_returns_502(self, client, token, db_session):
        uid = _get_user_id(token)
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _seed_google_creds(
            db_session, uid,
            access_token="expired-tok",
            refresh_token="good-refresh",
            expires_at=expired_at,
        )
        with patch("backend.config.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.config.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch("backend.routes.calendar.requests.post", side_effect=ConnectionError):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 502

    def test_refresh_failure_response_returns_401(self, client, token, db_session):
        uid = _get_user_id(token)
        expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _seed_google_creds(
            db_session, uid,
            access_token="expired-tok",
            refresh_token="bad-refresh",
            expires_at=expired_at,
        )
        with patch("backend.config.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.config.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch(
                "backend.routes.calendar.requests.post",
                return_value=_fake_ok_response({"error": "invalid_grant"}, status=401),
             ):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 401

    def test_mid_sync_401_triggers_inline_refresh(self, client, token, db_session):
        """
        If Google returns 401 mid-loop, the route should refresh inline and
        retry the same page successfully.
        """
        uid = _get_user_id(token)
        _seed_google_creds(db_session, uid)
        unauthorized = _fake_ok_response({}, status=401)
        events_resp = _fake_ok_response({"items": [_google_event()]})
        refresh_resp = _fake_ok_response({"access_token": "new-tok", "expires_in": 3600})

        get_responses = iter([unauthorized, events_resp])
        with patch("backend.config.GOOGLE_OAUTH_CLIENT_ID", "cid"), \
             patch("backend.config.GOOGLE_OAUTH_CLIENT_SECRET", "csec"), \
             patch("backend.routes.calendar.requests.post", return_value=refresh_resp), \
             patch("backend.routes.calendar.requests.get", side_effect=lambda *a, **kw: next(get_responses)):
            r = client.post("/calendar/google/sync", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["imported"] == 1
