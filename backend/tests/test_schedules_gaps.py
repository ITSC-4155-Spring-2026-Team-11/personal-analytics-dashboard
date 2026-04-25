"""
Coverage gaps for schedules.py:
  - prefs_to_dict with actual UserPreferences (the full dict return path)
  - get_tasks_for_date edge cases:
      invalid date → returns []
      daily recurrence task → always included
      weekly recurrence task on matching day → included
      weekly recurrence task on non-matching day → excluded
      fixed task with non-matching deadline → excluded
      semi task with future deadline not yet scheduled → included
  - GET /schedules/date/{date_str} with user preferences set (hits prefs_to_dict)
  - GET /schedules/date/{date_str} with invalid date format → 400
"""

from __future__ import annotations

import bootstrap_sys_path  # noqa: F401

from datetime import date, timedelta

import pytest

from backend.tests.helpers import auth_headers, login_form, register_verified_user


@pytest.fixture
def token(client):
    register_verified_user(client, email="schedgap@example.com",
                           password="SchedGap1", name="SchedGap")
    r = login_form(client, "schedgap@example.com", "SchedGap1")
    assert r.status_code == 200
    return r.json()["access_token"]


class TestGetTasksForDateDirectly:
    """Unit-level tests calling get_tasks_for_date directly to hit branches
    not reachable via the API (e.g., invalid date_str)."""

    def test_invalid_date_returns_empty_list(self, db_session):
        """get_tasks_for_date with a bad date string returns [] instead of raising."""
        from backend.routes.schedules import get_tasks_for_date
        result = get_tasks_for_date(user_id=999, date_str="not-a-date", db=db_session)
        assert result == []

    def test_valid_date_returns_list(self, db_session):
        """Smoke test: valid date with no tasks returns empty list."""
        from backend.routes.schedules import get_tasks_for_date
        result = get_tasks_for_date(user_id=999, date_str="2030-01-01", db=db_session)
        assert result == []


class TestGetTasksForDateRecurrence:
    """Verify the eligibility logic for recurring and semi-flexible tasks."""

    def test_daily_recurrence_task_always_included(self, client, token, db_session):
        """A daily recurring task appears on any date."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()

        task = Task(
            user_id=user.id, title="Daily task",
            recurrence="daily", recurrence_days=None,
            task_type="flexible", completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-03-15", db_session)
        ids = [t.id for t in result]
        assert task.id in ids

    def test_weekly_recurrence_matching_day_included(self, client, token, db_session):
        """Weekly task on a matching weekday is included."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        # 2030-03-04 is Monday (weekday 0)
        task = Task(
            user_id=user.id, title="Mon task",
            recurrence="weekly", recurrence_days="0",  # Monday
            task_type="flexible", completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-03-04", db_session)
        ids = [t.id for t in result]
        assert task.id in ids

    def test_weekly_recurrence_non_matching_day_excluded(self, client, token, db_session):
        """Weekly task on a non-matching weekday is excluded."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        # 2030-03-05 is Tuesday (weekday 1); task only runs Monday
        task = Task(
            user_id=user.id, title="Mon only",
            recurrence="weekly", recurrence_days="0",
            task_type="flexible", completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-03-05", db_session)
        ids = [t.id for t in result]
        assert task.id not in ids

    def test_fixed_task_matching_deadline_included(self, client, token, db_session):
        """Fixed task whose deadline matches the date is included."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        task = Task(
            user_id=user.id, title="Fixed meeting",
            task_type="fixed", fixed_start="09:00", fixed_end="10:00",
            deadline="2030-05-10", completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-05-10", db_session)
        ids = [t.id for t in result]
        assert task.id in ids

    def test_fixed_task_non_matching_deadline_excluded(self, client, token, db_session):
        """Fixed task whose deadline is a different date is excluded."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        task = Task(
            user_id=user.id, title="Fixed meeting 2",
            task_type="fixed", fixed_start="09:00", fixed_end="10:00",
            deadline="2030-05-10", completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-05-11", db_session)
        ids = [t.id for t in result]
        assert task.id not in ids

    def test_semi_task_with_future_deadline_included_once(self, client, token, db_session):
        """Semi task with a future deadline and no prior scheduling is included."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        task = Task(
            user_id=user.id, title="Semi future",
            task_type="semi", deadline="2030-12-31",
            last_scheduled_date=None, completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-06-01", db_session)
        ids = [t.id for t in result]
        assert task.id in ids

    def test_semi_task_already_scheduled_today_excluded(self, client, token, db_session):
        """Semi task with last_scheduled_date == today is NOT re-included."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        today = "2030-06-01"
        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        task = Task(
            user_id=user.id, title="Semi already done",
            task_type="semi", deadline="2030-12-31",
            last_scheduled_date=today, completed=False,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, today, db_session)
        ids = [t.id for t in result]
        assert task.id not in ids

    def test_completed_task_excluded(self, client, token, db_session):
        """Completed tasks are never returned by get_tasks_for_date."""
        from backend.routes.schedules import get_tasks_for_date
        from backend.models import Task, User

        user = db_session.query(User).filter_by(email="schedgap@example.com").first()
        task = Task(
            user_id=user.id, title="Done task",
            task_type="flexible", completed=True,
        )
        db_session.add(task)
        db_session.commit()

        result = get_tasks_for_date(user.id, "2030-01-01", db_session)
        ids = [t.id for t in result]
        assert task.id not in ids


class TestPrefsToDict:
    """Test prefs_to_dict with actual UserPreferences (the full dict return)."""

    def test_prefs_to_dict_none_returns_empty(self):
        from backend.routes.schedules import prefs_to_dict
        assert prefs_to_dict(None) == {}

    def test_prefs_to_dict_with_prefs_returns_full_dict(self, db_session):
        """With a real UserPreferences object, all keys are present."""
        from backend.routes.schedules import prefs_to_dict
        from backend.models import UserPreferences

        prefs = UserPreferences(user_id=0)
        prefs.wake_time = "06:30"
        prefs.sleep_time = "22:30"
        prefs.chronotype = "morning"
        prefs.schedule_density = "packed"
        prefs.preferred_buffer_minutes = 15
        prefs.energy_morning_high = 0.8
        prefs.energy_morning_medium = 0.7
        prefs.energy_morning_low = 0.5
        prefs.energy_afternoon_high = 0.5
        prefs.energy_afternoon_medium = 0.6
        prefs.energy_afternoon_low = 0.6
        prefs.energy_evening_high = 0.3
        prefs.energy_evening_medium = 0.5
        prefs.energy_evening_low = 0.8

        result = prefs_to_dict(prefs)
        assert result["wake_time"] == "06:30"
        assert result["sleep_time"] == "22:30"
        assert result["chronotype"] == "morning"
        assert result["preferred_buffer_minutes"] == 15
        assert result["energy_morning_high"] == 0.8
        assert result["energy_evening_low"] == 0.8

        expected_keys = {
            "wake_time", "sleep_time", "chronotype", "schedule_density",
            "preferred_buffer_minutes",
            "energy_morning_high", "energy_morning_medium", "energy_morning_low",
            "energy_afternoon_high", "energy_afternoon_medium", "energy_afternoon_low",
            "energy_evening_high", "energy_evening_medium", "energy_evening_low",
        }
        assert expected_keys == set(result.keys())


class TestScheduleAPIWithPreferences:
    """Hit the schedule endpoint with user preferences set to exercise prefs_to_dict."""

    def test_schedule_with_preferences_set(self, client, token):
        """After setting preferences, /schedules/today uses them (prefs_to_dict called)."""
        # Set preferences first
        client.put("/preferences", headers=auth_headers(token),
                   json={"wake_time": "08:00", "sleep_time": "22:00",
                         "chronotype": "morning"})

        r = client.get("/schedules/today", headers=auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "scheduled" in data
        assert "overflow" in data

    def test_schedule_date_invalid_format_returns_400(self, client, token):
        r = client.get("/schedules/date/notadate", headers=auth_headers(token))
        assert r.status_code == 400

    def test_schedule_date_valid_future_date(self, client, token):
        future = (date.today() + timedelta(days=10)).isoformat()
        r = client.get(f"/schedules/date/{future}", headers=auth_headers(token))
        assert r.status_code == 200

    def test_reschedule_increments_times_rescheduled(self, client, token):
        tid = client.post("/tasks/", headers=auth_headers(token),
                          json={"title": "Reschedule me",
                                "deadline": date.today().isoformat()},
                          ).json()["task"]["id"]

        r = client.post(f"/schedules/reschedule/{tid}", headers=auth_headers(token))
        assert r.status_code == 200

        # Confirm times_rescheduled incremented
        task_r = client.get(f"/tasks/{tid}", headers=auth_headers(token))
        assert task_r.json()["times_rescheduled"] == 1

    def test_schedule_with_fixed_task_having_prefs(self, client, token):
        """Fixed task on today + user prefs: exercises full prefs_to_dict path."""
        today = date.today().isoformat()
        client.put("/preferences", headers=auth_headers(token),
                   json={"wake_time": "07:00", "sleep_time": "23:00"})
        client.post("/tasks/", headers=auth_headers(token),
                    json={"title": "Doctor",
                          "task_type": "fixed",
                          "fixed_start": "10:00",
                          "fixed_end": "11:00",
                          "deadline": today})

        r = client.get("/schedules/today", headers=auth_headers(token))
        assert r.status_code == 200
