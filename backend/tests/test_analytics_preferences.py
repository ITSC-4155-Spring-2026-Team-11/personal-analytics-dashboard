"""
Complete coverage for analytics.py and preferences.py routes.

analytics.py:
  GET /analytics/daily?date=YYYY-MM-DD
  _format_duration helper

preferences.py:
  GET /preferences
  GET /preferences/figures
  PUT /preferences
  _weight_label helper (tested via /figures)
  _get_or_create_prefs (tested via GET)
"""

from __future__ import annotations

import bootstrap_sys_path  # noqa: F401

from datetime import datetime, timezone, date, timedelta

import pytest

from backend.tests.helpers import auth_headers, login_form, register_verified_user


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def token(client):
    register_verified_user(client, email="anlpref@example.com", password="AnlPref1", name="AnlPref")
    r = login_form(client, "anlpref@example.com", "AnlPref1")
    assert r.status_code == 200
    return r.json()["access_token"]


# ── _format_duration unit tests ────────────────────────────────────────────────

class TestFormatDuration:
    """Test the internal _format_duration helper directly and via the analytics endpoint."""

    def test_zero_minutes_returns_0m(self):
        """0 minutes → '0m' (tests via direct import)."""
        from backend.routes.analytics import _format_duration
        assert _format_duration(0) == "0m"

    def test_direct_import_minutes_only(self):
        """30 minutes → '30m'."""
        from backend.routes.analytics import _format_duration
        assert _format_duration(30) == "30m"

    def test_direct_import_exact_hour(self):
        """60 minutes → '1h'."""
        from backend.routes.analytics import _format_duration
        assert _format_duration(60) == "1h"

    def test_direct_import_hours_and_minutes(self):
        """90 minutes → '1h 30m'."""
        from backend.routes.analytics import _format_duration
        assert _format_duration(90) == "1h 30m"

    def test_minutes_only_returns_Xm(self, client, token):
        """30 minutes → '30m'."""
        today = date.today().isoformat()
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "Short", "duration_minutes": 30,
                                "deadline": today}).json()["task"]["id"]
        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        tasks = r.json()["tasks"]
        t = next(t for t in tasks if t["id"] == tid)
        assert t["duration_label"] == "30m"

    def test_exact_hour_returns_Xh(self, client, token):
        """60 minutes → '1h'."""
        today = date.today().isoformat()
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "Hour", "duration_minutes": 60,
                                "deadline": today}).json()["task"]["id"]
        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        tasks = r.json()["tasks"]
        t = next(t for t in tasks if t["id"] == tid)
        assert t["duration_label"] == "1h"

    def test_hours_and_minutes_returns_XhYm(self, client, token):
        """90 minutes → '1h 30m'."""
        today = date.today().isoformat()
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "HourHalf", "duration_minutes": 90,
                                "deadline": today}).json()["task"]["id"]
        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        tasks = r.json()["tasks"]
        t = next(t for t in tasks if t["id"] == tid)
        assert t["duration_label"] == "1h 30m"

    def test_two_hours_exact(self, client, token):
        """120 minutes → '2h'."""
        today = date.today().isoformat()
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "TwoHours", "duration_minutes": 120,
                                "deadline": today}).json()["task"]["id"]
        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        tasks = r.json()["tasks"]
        t = next(t for t in tasks if t["id"] == tid)
        assert t["duration_label"] == "2h"


# ── GET /analytics/daily ───────────────────────────────────────────────────────

class TestAnalyticsDailySummary:

    def test_requires_auth(self, client):
        r = client.get("/analytics/daily?date=2030-01-01")
        assert r.status_code == 401

    def test_empty_day_returns_empty_tasks(self, client, token):
        r = client.get("/analytics/daily?date=2099-01-01", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert data["tasks"] == []
        assert data["total_minutes"] == 0
        assert data["task_count"] == 0
        assert data["by_category"] == {}

    def test_task_with_matching_deadline_is_included(self, client, token):
        """Task whose deadline == date appears in the summary."""
        target = "2030-06-15"
        r_create = client.post("/tasks/", headers=auth_headers(token),
                               json={"title": "Deadline task", "deadline": target,
                                     "duration_minutes": 45})
        assert r_create.status_code == 201

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        titles = [t["title"] for t in data["tasks"]]
        assert "Deadline task" in titles
        assert data["total_minutes"] == 45
        assert data["task_count"] == 1

    def test_completed_task_on_date_is_included(self, client, token):
        """Task completed today appears via completed_at date match."""
        today = date.today().isoformat()
        # Create and complete
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "Completed today", "duration_minutes": 30}
                          ).json()["task"]["id"]
        client.post(f"/tasks/{tid}/complete", headers=auth_headers(token))

        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        data = r.json()
        titles = [t["title"] for t in data["tasks"]]
        assert "Completed today" in titles

    def test_task_not_counted_twice_when_deadline_and_completed_same_day(self, client, token):
        """A task whose deadline==date AND completed_at==date appears only once."""
        today = date.today().isoformat()
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "Double", "deadline": today,
                                "duration_minutes": 20}).json()["task"]["id"]
        client.post(f"/tasks/{tid}/complete", headers=auth_headers(token))

        r = client.get(f"/analytics/daily?date={today}", headers=auth_headers(token))
        data = r.json()
        ids = [t["id"] for t in data["tasks"]]
        assert ids.count(tid) == 1

    def test_by_category_breakdown(self, client, token):
        """Multiple categories are summed correctly in by_category."""
        target = "2030-07-04"
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Work task", "category": "Work",
                          "duration_minutes": 60, "deadline": target})
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Study task", "category": "Study",
                          "duration_minutes": 45, "deadline": target})
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Exercise task", "category": "Exercise",
                          "duration_minutes": 30, "deadline": target})

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        data = r.json()
        by_cat = data["by_category"]
        assert by_cat["Work"] == 60
        assert by_cat["Study"] == 45
        assert by_cat["Exercise"] == 30
        assert data["total_minutes"] == 135

    def test_total_formatted_multi_hour(self, client, token):
        """total_formatted shows correct 'Xh Ym' format."""
        target = "2030-08-10"
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Long task", "duration_minutes": 150, "deadline": target})

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        data = r.json()
        assert data["total_formatted"] == "2h 30m"

    def test_task_fields_in_response(self, client, token):
        """Each task in the response has required fields."""
        target = "2030-09-01"
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Field check", "duration_minutes": 30,
                          "deadline": target, "importance": 4, "task_type": "semi",
                          "fixed_start": None})

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        task = r.json()["tasks"][0]
        for field in ("id", "title", "category", "duration_minutes", "duration_label",
                      "completed", "task_type", "fixed_start", "fixed_end", "importance"):
            assert field in task, f"Field '{field}' missing from analytics response"

    def test_tasks_for_other_users_not_included(self, client, token):
        """Tasks belonging to a different user do not appear."""
        target = "2030-10-01"
        # Create task for primary user
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "My task", "deadline": target})

        # Register another user and create a task
        register_verified_user(client, email="other2@example.com", password="Other2Pass1")
        other_tok = login_form(client, "other2@example.com", "Other2Pass1").json()["access_token"]
        client.post("/tasks/", headers=auth_headers(other_tok),
                    json={"title": "Their task", "deadline": target})

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        titles = [t["title"] for t in r.json()["tasks"]]
        assert "My task" in titles
        assert "Their task" not in titles

    def test_uncompleted_task_not_included_via_completed_at(self, client, token):
        """An incomplete task with no deadline on this date is not included."""
        target = "2030-11-01"
        # Task with a different deadline
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Different date", "deadline": "2030-12-31"})

        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        titles = [t["title"] for t in r.json()["tasks"]]
        assert "Different date" not in titles

    def test_date_key_in_response(self, client, token):
        """Response includes the queried date."""
        target = "2030-12-25"
        r = client.get(f"/analytics/daily?date={target}", headers=auth_headers(token))
        assert r.json()["date"] == target


# ── GET /preferences ───────────────────────────────────────────────────────────

class TestGetPreferences:

    def test_requires_auth(self, client):
        r = client.get("/preferences")
        assert r.status_code == 401

    def test_creates_defaults_for_new_user(self, client, token):
        """First GET auto-creates a UserPreferences row with defaults."""
        r = client.get("/preferences", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert data["wake_time"] == "07:00"
        assert data["sleep_time"] == "23:00"
        assert data["chronotype"] == "neutral"
        assert data["timezone"] == "UTC"
        assert data["schedule_density"] == "relaxed"
        assert data["preferred_buffer_minutes"] == 10

    def test_returns_all_energy_weight_fields(self, client, token):
        """All 9 energy weight fields are present and between 0 and 1."""
        r = client.get("/preferences", headers=auth_headers(token))
        data = r.json()
        for period in ("morning", "afternoon", "evening"):
            for level in ("high", "medium", "low"):
                key = f"energy_{period}_{level}"
                assert key in data, f"Missing field: {key}"
                assert 0.0 <= data[key] <= 1.0

    def test_second_get_returns_same_row(self, client, token):
        """Calling GET twice does not create duplicate rows."""
        r1 = client.get("/preferences", headers=auth_headers(token))
        r2 = client.get("/preferences", headers=auth_headers(token))
        assert r1.json()["wake_time"] == r2.json()["wake_time"]

    def test_user_id_in_response(self, client, token):
        r = client.get("/preferences", headers=auth_headers(token))
        assert "user_id" in r.json()


# ── PUT /preferences ───────────────────────────────────────────────────────────

class TestUpdatePreferences:

    def test_update_wake_time(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"wake_time": "06:30"})
        assert r.status_code == 200
        assert r.json()["wake_time"] == "06:30"

    def test_update_sleep_time(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"sleep_time": "22:00"})
        assert r.status_code == 200
        assert r.json()["sleep_time"] == "22:00"

    def test_update_chronotype_morning(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"chronotype": "morning"})
        assert r.status_code == 200
        assert r.json()["chronotype"] == "morning"

    def test_update_chronotype_evening(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"chronotype": "evening"})
        assert r.status_code == 200
        assert r.json()["chronotype"] == "evening"

    def test_update_timezone(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"timezone": "America/New_York"})
        assert r.status_code == 200
        assert r.json()["timezone"] == "America/New_York"

    def test_partial_update_leaves_others_unchanged(self, client, token):
        """Updating only wake_time does not change sleep_time."""
        client.put("/preferences", headers=auth_headers(token),
                   json={"sleep_time": "00:30"})
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"wake_time": "05:00"})
        assert r.json()["sleep_time"] == "00:30"
        assert r.json()["wake_time"] == "05:00"

    def test_invalid_chronotype_returns_422(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"chronotype": "zombie"})
        assert r.status_code == 422

    def test_invalid_wake_time_format_returns_422(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"wake_time": "7am"})
        assert r.status_code == 422

    def test_invalid_wake_time_out_of_range_returns_422(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"wake_time": "25:00"})
        assert r.status_code == 422

    def test_invalid_sleep_time_missing_colon_returns_422(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"sleep_time": "2300"})
        assert r.status_code == 422

    def test_saved_key_in_response(self, client, token):
        r = client.put("/preferences", headers=auth_headers(token),
                       json={"chronotype": "neutral"})
        assert r.json()["saved"] is True

    def test_requires_auth(self, client):
        r = client.put("/preferences", json={"wake_time": "07:00"})
        assert r.status_code == 401


# ── GET /preferences/figures ───────────────────────────────────────────────────

class TestPreferenceFigures:

    def test_requires_auth(self, client):
        r = client.get("/preferences/figures")
        assert r.status_code == 401

    def test_returns_energy_curve_structure(self, client, token):
        """energy_curve has morning/afternoon/evening × high/medium/low."""
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.status_code == 200
        ec = r.json()["energy_curve"]
        for period in ("morning", "afternoon", "evening"):
            assert period in ec
            for level in ("high", "medium", "low"):
                assert level in ec[period]
                cell = ec[period][level]
                assert "weight" in cell
                assert "label" in cell

    def test_weight_label_values(self, client, token):
        """Each cell label is one of the known categories."""
        valid_labels = {"excellent", "good", "neutral", "below average", "poor"}
        r = client.get("/preferences/figures", headers=auth_headers(token))
        ec = r.json()["energy_curve"]
        for period in ("morning", "afternoon", "evening"):
            for level in ("high", "medium", "low"):
                assert ec[period][level]["label"] in valid_labels

    def test_returns_schedule_settings(self, client, token):
        r = client.get("/preferences/figures", headers=auth_headers(token))
        ss = r.json()["schedule_settings"]
        for key in ("wake_time", "sleep_time", "chronotype", "timezone",
                    "schedule_density", "preferred_buffer_minutes"):
            assert key in ss

    def test_returns_summary_list(self, client, token):
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert isinstance(r.json()["summary"], list)

    def test_summary_contains_density_insight(self, client, token):
        """With default 'relaxed' density, summary says 'breathing room'."""
        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "breathing room" in summary

    def test_summary_packed_density(self, client, token, db_session):
        """With 'packed' density, summary says 'packed schedule'."""
        from backend.models import UserPreferences
        # Ensure prefs exist first
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.schedule_density = "packed"
            db_session.commit()

        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "packed" in summary

    def test_summary_best_high_energy_period(self, client, token, db_session):
        """When energy_morning_high > 0.5, summary mentions morning."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.9
            prefs.energy_afternoon_high = 0.3
            prefs.energy_evening_high = 0.2
            db_session.commit()

        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "morning" in summary

    def test_summary_worst_high_energy_period(self, client, token, db_session):
        """When the minimum high energy weight < 0.5, summary mentions avoiding it."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.9
            prefs.energy_afternoon_high = 0.8
            prefs.energy_evening_high = 0.1  # worst
            db_session.commit()

        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "avoid" in summary

    def test_summary_large_buffer(self, client, token, db_session):
        """When buffer >= 20 minutes, summary mentions the buffer."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.preferred_buffer_minutes = 25
            db_session.commit()

        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "25 min" in summary or "buffers" in summary

    def test_summary_morning_chronotype(self, client, token):
        """After updating chronotype to morning, summary mentions morning person."""
        client.put("/preferences", headers=auth_headers(token),
                   json={"chronotype": "morning"})
        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "morning person" in summary

    def test_summary_evening_chronotype(self, client, token):
        """After updating chronotype to evening, summary mentions evening person."""
        client.put("/preferences", headers=auth_headers(token),
                   json={"chronotype": "evening"})
        r = client.get("/preferences/figures", headers=auth_headers(token))
        summary = " ".join(r.json()["summary"]).lower()
        assert "evening person" in summary

    def test_user_id_in_response(self, client, token):
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert "user_id" in r.json()

    def test_weight_label_excellent_threshold(self, client, token, db_session):
        """Weight >= 0.75 → 'excellent'."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.80
            db_session.commit()
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.json()["energy_curve"]["morning"]["high"]["label"] == "excellent"

    def test_weight_label_good_threshold(self, client, token, db_session):
        """Weight 0.55-0.74 → 'good'."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.60
            db_session.commit()
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.json()["energy_curve"]["morning"]["high"]["label"] == "good"

    def test_weight_label_neutral_threshold(self, client, token, db_session):
        """Weight 0.40-0.54 → 'neutral'."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.45
            db_session.commit()
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.json()["energy_curve"]["morning"]["high"]["label"] == "neutral"

    def test_weight_label_below_average_threshold(self, client, token, db_session):
        """Weight 0.25-0.39 → 'below average'."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.30
            db_session.commit()
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.json()["energy_curve"]["morning"]["high"]["label"] == "below average"

    def test_weight_label_poor_threshold(self, client, token, db_session):
        """Weight < 0.25 → 'poor'."""
        from backend.models import UserPreferences
        client.get("/preferences", headers=auth_headers(token))
        prefs = db_session.query(UserPreferences).first()
        if prefs:
            prefs.energy_morning_high = 0.10
            db_session.commit()
        r = client.get("/preferences/figures", headers=auth_headers(token))
        assert r.json()["energy_curve"]["morning"]["high"]["label"] == "poor"
