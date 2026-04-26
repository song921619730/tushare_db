"""Scheduler jobs unit tests (mock only).

Covers: _is_trading_day, run_batch, run_saturday_longtail,
run_refresh_reference, run_weekly_reconcile, run_verify_row_counts.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestIsTradingDay:
    """jobs.py — _is_trading_day."""

    def test_trading_day_true(self):
        from tushare_db.scheduler.jobs import _is_trading_day

        client = MagicMock()
        client.query.return_value.result_rows = [(1,)]
        assert _is_trading_day(client, "20240101") is True

    def test_trading_day_false(self):
        from tushare_db.scheduler.jobs import _is_trading_day

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(13161,)]),
        ]
        assert _is_trading_day(client, "20240101") is False

    def test_empty_trade_cal_raises(self):
        from tushare_db.scheduler.jobs import _is_trading_day

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(0,)]),
        ]
        with pytest.raises(RuntimeError, match="bootstrap"):
            _is_trading_day(client, "20240101")

    def test_empty_result_rows(self):
        from tushare_db.scheduler.jobs import _is_trading_day

        client = MagicMock()
        client.query.return_value.result_rows = []
        assert _is_trading_day(client, "20240101") is False


class TestRunBatch:
    """jobs.py — run_batch."""

    def test_skips_non_trading_day(self):
        from tushare_db.scheduler.jobs import run_batch

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(10000,)]),
        ]

        result = run_batch("A", ch_client=client, tushare_client=MagicMock())

        assert result["skipped"] is True
        assert result["reason"] == "non_trading_day"

    def test_reference_runs_on_non_trading_day(self):
        """Reference batch bypasses trading day check."""
        from tushare_db.scheduler.jobs import run_batch

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(10000,)]),
        ]

        with patch("tushare_db.scheduler.jobs.run_incremental") as mock_run:
            mock_run.return_value = {"total": 5, "done": 5, "failed": 0}
            result = run_batch("reference", ch_client=client, tushare_client=MagicMock())

        assert "skipped" not in result
        assert result["total"] == 5

    def test_saturday_runs_on_non_trading_day(self):
        from tushare_db.scheduler.jobs import run_batch

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(10000,)]),
        ]

        with patch("tushare_db.scheduler.jobs.run_incremental") as mock_run:
            mock_run.return_value = {"total": 3, "done": 3, "failed": 0}
            result = run_batch("saturday", ch_client=client, tushare_client=MagicMock())

        assert "skipped" not in result

    def test_trading_day_runs_incremental(self):
        from tushare_db.scheduler.jobs import run_batch

        client = MagicMock()
        tushare = MagicMock()
        client.query.return_value.result_rows = [(1,)]

        with patch("tushare_db.scheduler.jobs.run_incremental") as mock_run:
            mock_run.return_value = {"total": 10, "done": 10, "failed": 0}
            result = run_batch("B", ch_client=client, tushare_client=tushare)

        mock_run.assert_called_once()
        assert result["total"] == 10

    def test_creates_and_cleans_client(self):
        from tushare_db.scheduler.jobs import run_batch

        with patch("tushare_db.scheduler.jobs._is_trading_day", return_value=True), \
             patch("tushare_db.scheduler.jobs.run_incremental") as mock_run, \
             patch("tushare_db.scheduler.jobs._get_ch_client") as mock_get_ch, \
             patch("tushare_db.scheduler.jobs._get_tushare_client") as mock_get_ts:
            mock_run.return_value = {"total": 0, "done": 0, "failed": 0}
            mock_client = MagicMock()
            mock_get_ch.return_value = mock_client
            mock_get_ts.return_value = MagicMock()

            run_batch("A")
            mock_client.close.assert_called_once()


class TestRunSaturdayLongtail:
    """jobs.py — run_saturday_longtail."""

    def test_no_per_symbol_specs(self):
        """No per_symbol_period interfaces → skipped."""
        from tushare_db.scheduler.jobs import run_saturday_longtail

        client = MagicMock()
        mock_spec = MagicMock()
        mock_spec.enabled = True
        mock_spec.fetch_strategy = MagicMock()
        mock_spec.fetch_strategy.kind = "date_loop"

        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[mock_spec]):
            result = run_saturday_longtail(ch_client=client, tushare_client=MagicMock())

        assert result["skipped"] is True
        assert result["reason"] == "no_per_symbol_specs"

    def test_no_target_date(self):
        from tushare_db.scheduler.jobs import run_saturday_longtail

        client = MagicMock()
        mock_spec = MagicMock()
        mock_spec.enabled = True
        mock_spec.fetch_strategy = MagicMock()
        mock_spec.fetch_strategy.kind = "per_symbol_period"

        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[mock_spec]), \
             patch("tushare_db.scheduler.jobs.get_target_date", return_value=None):
            result = run_saturday_longtail(ch_client=client, tushare_client=MagicMock())

        assert result["skipped"] is True
        assert result["reason"] == "no_target_date"

    def test_creates_and_cleans_client(self):
        from tushare_db.scheduler.jobs import run_saturday_longtail

        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[]), \
             patch("tushare_db.scheduler.jobs._get_ch_client") as mock_get_ch:
            mock_client = MagicMock()
            mock_get_ch.return_value = mock_client

            run_saturday_longtail(tushare_client=MagicMock())
            mock_client.close.assert_called_once()

    def test_delegates_to_plan_and_execute(self):
        """With per_symbol specs, runs plan_units + execute_batch."""
        from tushare_db.scheduler.jobs import run_saturday_longtail

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[(10000,)]),
        ]

        mock_spec = MagicMock()
        mock_spec.enabled = True
        mock_spec.name = "test_per_symbol"
        mock_spec.fetch_strategy = MagicMock()
        mock_spec.fetch_strategy.kind = "per_symbol_period"

        mock_unit = MagicMock()
        mock_unit.interface = "test"
        mock_unit.scope_key = "test:1"
        mock_unit.bucket = "normal"
        mock_unit.retries = 0

        # plan_units and execute_batch are local imports inside the function
        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[mock_spec]), \
             patch("tushare_db.scheduler.jobs.get_target_date", return_value="20240101"), \
             patch("tushare_db.planner.planner.plan_units", return_value=[mock_unit]), \
             patch("tushare_db.runner.executor.execute_batch", return_value=(1, 1, 0)):
            result = run_saturday_longtail(ch_client=client, tushare_client=MagicMock())

        assert result["total"] == 1
        assert result["done"] == 1


class TestRunRefreshReference:
    """jobs.py — run_refresh_reference."""

    def test_delegates_to_run_batch(self):
        from tushare_db.scheduler.jobs import run_refresh_reference

        with patch("tushare_db.scheduler.jobs.run_batch") as mock_run:
            mock_run.return_value = {"total": 3, "done": 3}
            result = run_refresh_reference(ch_client=MagicMock(), tushare_client=MagicMock())

            mock_run.assert_called_once()


class TestRunWeeklyReconcile:
    """jobs.py — run_weekly_reconcile."""

    def test_no_pending_units(self):
        from tushare_db.scheduler.jobs import run_weekly_reconcile

        client = MagicMock()
        p0 = MagicMock(enabled=True, name="daily", priority="P0")
        p1 = MagicMock(enabled=True, name="weekly", priority="P1")
        disabled = MagicMock(enabled=False, name="ghost", priority="P0")

        # get_pending_units is a local import inside the function
        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[p0, p1, disabled]), \
             patch("tushare_db.meta.sync_state.get_pending_units", return_value=[]):
            result = run_weekly_reconcile(ch_client=client)

        assert result["interfaces_scanned"] == 2
        assert result["total_pending"] == 0

    def test_pending_units_counted(self):
        from tushare_db.scheduler.jobs import run_weekly_reconcile

        client = MagicMock()
        spec = MagicMock(enabled=True, name="daily", priority="P0")

        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[spec]), \
             patch("tushare_db.meta.sync_state.get_pending_units") as mock_pending:
            mock_pending.return_value = [
                {"scope_key": "daily:20240101", "status": "failed", "attempts": 3},
                {"scope_key": "daily:20240102", "status": "partial", "attempts": 1},
            ]
            result = run_weekly_reconcile(ch_client=client)

        assert result["total_pending"] == 2

    def test_creates_and_cleans_client(self):
        from tushare_db.scheduler.jobs import run_weekly_reconcile

        with patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[]), \
             patch("tushare_db.scheduler.jobs._get_ch_client") as mock_get_ch:
            mock_client = MagicMock()
            mock_get_ch.return_value = mock_client

            run_weekly_reconcile()
            mock_client.close.assert_called_once()


class TestRunVerifyRowCounts:
    """jobs.py — run_verify_row_counts."""

    def test_no_target_date(self):
        from tushare_db.scheduler.jobs import run_verify_row_counts

        client = MagicMock()
        with patch("tushare_db.scheduler.jobs.get_target_date", return_value=None):
            result = run_verify_row_counts(ch_client=client)

        assert result["skipped"] is True
        assert result["reason"] == "no_target_date"

    def test_non_trading_day(self):
        from tushare_db.scheduler.jobs import run_verify_row_counts

        client = MagicMock()
        with patch("tushare_db.scheduler.jobs.get_target_date", return_value="20240101"), \
             patch("tushare_db.scheduler.jobs._is_trading_day", return_value=False):
            result = run_verify_row_counts(ch_client=client)

        assert result["skipped"] is True
        assert result["reason"] == "non_trading_day"

    def test_trading_day_checks_zero_rows(self):
        from tushare_db.scheduler.jobs import run_verify_row_counts

        client = MagicMock()
        client.query.return_value.result_rows = [(100,)]

        spec = MagicMock(enabled=True, name="daily")

        with patch("tushare_db.scheduler.jobs.get_target_date", return_value="20240101"), \
             patch("tushare_db.scheduler.jobs._is_trading_day", return_value=True), \
             patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[spec]):
            result = run_verify_row_counts(ch_client=client)

        assert result["zero_count"] == 0
        assert result["interfaces_checked"] == 1

    def test_zero_row_interface_reported(self):
        from tushare_db.scheduler.jobs import run_verify_row_counts

        client = MagicMock()
        client.query.return_value.result_rows = [(0,)]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "broken_daily"  # Real string, not MagicMock

        with patch("tushare_db.scheduler.jobs.get_target_date", return_value="20240101"), \
             patch("tushare_db.scheduler.jobs._is_trading_day", return_value=True), \
             patch("tushare_db.scheduler.jobs.load_interface_specs", return_value=[spec]):
            result = run_verify_row_counts(ch_client=client)

        assert result["zero_count"] == 1
        assert "broken_daily" in result["zero_interfaces"]


class TestRunWeeklyBackup:
    """jobs.py — run_weekly_backup."""

    def test_backup_success(self):
        from tushare_db.scheduler.jobs import run_weekly_backup

        client = MagicMock()
        client.command.return_value = True

        result = run_weekly_backup(ch_client=client)

        assert result["status"] == "success"
        assert "backup_name" in result
        assert result["backup_name"].startswith("tushare_")
        client.command.assert_called_once()
        sql = client.command.call_args[0][0]
        assert "BACKUP DATABASE tushare" in sql
        assert "Disk('backups'" in sql

    def test_backup_failure(self):
        from tushare_db.scheduler.jobs import run_weekly_backup

        client = MagicMock()
        client.command.side_effect = Exception("Disk 'backups' not found")

        result = run_weekly_backup(ch_client=client)

        assert result["status"] == "failed"
        assert "error" in result

    def test_backup_creates_and_closes_client(self):
        from tushare_db.scheduler.jobs import run_weekly_backup

        with patch("tushare_db.scheduler.jobs._get_ch_client") as mock_get:
            mock_client = MagicMock()
            mock_client.command.return_value = True
            mock_get.return_value = mock_client

            result = run_weekly_backup()

            assert result["status"] == "success"
            mock_client.close.assert_called_once()


class TestServiceRegistersBackup:
    """scheduler/service.py should register the weekly_backup job."""

    def test_service_has_weekly_backup_job(self):
        from tushare_db.scheduler.service import create_scheduler

        scheduler = create_scheduler()
        job_ids = [j.id for j in scheduler.get_jobs()]
        assert "weekly_backup" in job_ids, f"Expected weekly_backup in {job_ids}"
