"""Unit tests for scheduler service and jobs."""

from __future__ import annotations

import zoneinfo
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tushare_db.scheduler.service import create_scheduler


class TestSchedulerService:
    """Test the scheduler service."""

    def test_create_scheduler_registers_all_jobs(self):
        """Verify all expected jobs are registered."""
        scheduler = create_scheduler()
        jobs = scheduler.get_jobs()
        job_ids = {j.id for j in jobs}

        expected = {
            "batch_a",
            "batch_b",
            "batch_c",
            "batch_d",
            "saturday_longtail",
            "refresh_reference",
            "weekly_reconcile",
            "verify_row_counts",
        }
        assert expected.issubset(job_ids)

    def test_scheduler_uses_asia_shanghai_timezone(self):
        """Verify scheduler uses Asia/Shanghai timezone."""
        scheduler = create_scheduler()
        assert str(scheduler.timezone) == "Asia/Shanghai"

    def _get_field_value(self, trigger, name: str) -> str:
        """Get the string value of a cron trigger field."""
        for f in trigger.fields:
            if f.name == name:
                return str(f)
        return ""

    def test_batch_a_runs_at_17_00_weekdays(self):
        """Verify batch A triggers at 17:00 Mon-Fri."""
        scheduler = create_scheduler()
        batch_a = scheduler.get_job("batch_a")
        assert batch_a is not None
        trigger = batch_a.trigger
        assert "17" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")
        assert "mon-fri" in self._get_field_value(trigger, "day_of_week").lower()

    def test_batch_b_runs_at_18_00_weekdays(self):
        """Verify batch B triggers at 18:00 Mon-Fri."""
        scheduler = create_scheduler()
        batch_b = scheduler.get_job("batch_b")
        assert batch_b is not None
        trigger = batch_b.trigger
        assert "18" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")

    def test_saturday_longtail_runs_at_02_00_sat(self):
        """Verify Saturday long-tail triggers at 02:00."""
        scheduler = create_scheduler()
        job = scheduler.get_job("saturday_longtail")
        assert job is not None
        trigger = job.trigger
        assert "2" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")
        assert "sat" in self._get_field_value(trigger, "day_of_week").lower()

    def test_refresh_reference_runs_at_06_00_daily(self):
        """Verify refresh_reference runs at 06:00 daily."""
        scheduler = create_scheduler()
        job = scheduler.get_job("refresh_reference")
        assert job is not None
        trigger = job.trigger
        assert "6" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")

    def test_weekly_reconcile_runs_at_02_00_sun(self):
        """Verify weekly_reconcile runs at 02:00 Sun."""
        scheduler = create_scheduler()
        job = scheduler.get_job("weekly_reconcile")
        assert job is not None
        trigger = job.trigger
        assert "2" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")
        assert "sun" in self._get_field_value(trigger, "day_of_week").lower()

    def test_verify_row_counts_runs_at_03_00_daily(self):
        """Verify verify_row_counts runs at 03:00 daily."""
        scheduler = create_scheduler()
        job = scheduler.get_job("verify_row_counts")
        assert job is not None
        trigger = job.trigger
        assert "3" in self._get_field_value(trigger, "hour")
        assert "0" in self._get_field_value(trigger, "minute")

    def test_all_jobs_have_misfire_grace_time(self):
        """Verify all jobs have 1 hour misfire grace time."""
        scheduler = create_scheduler()
        for job in scheduler.get_jobs():
            assert job.misfire_grace_time == 3600, f"Job {job.id} missing misfire_grace_time"

    def test_all_jobs_have_coalesce(self):
        """Verify all jobs have coalesce enabled."""
        scheduler = create_scheduler()
        for job in scheduler.get_jobs():
            assert job.coalesce is True, f"Job {job.id} should have coalesce=True"

    def test_all_jobs_have_max_instances_1(self):
        """Verify all jobs have max_instances=1 to prevent concurrent runs."""
        scheduler = create_scheduler()
        for job in scheduler.get_jobs():
            assert job.max_instances == 1, f"Job {job.id} should have max_instances=1"
