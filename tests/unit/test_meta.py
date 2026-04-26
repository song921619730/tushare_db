"""Meta module unit tests: sync_state, sync_runs (mock only)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestMarkStaleUnits:
    """sync_state.py — mark_stale_units."""

    def test_no_stale_units(self):
        from tushare_db.meta.sync_state import mark_stale_units

        client = MagicMock()
        client.command.return_value = 0
        result = mark_stale_units(client)
        assert result == 0

    def test_stale_units_marked(self):
        from tushare_db.meta.sync_state import mark_stale_units

        client = MagicMock()
        client.command.side_effect = [5, None]
        result = mark_stale_units(client, threshold_minutes=5)
        assert result == 5
        assert client.command.call_count == 2

    def test_custom_threshold(self):
        from tushare_db.meta.sync_state import mark_stale_units

        client = MagicMock()
        client.command.return_value = 3

        mark_stale_units(client, threshold_minutes=15)

        first_call = client.command.call_args_list[0][0][0]
        assert "INTERVAL 15 MINUTE" in first_call

    def test_query_uses_asia_shanghai(self):
        from tushare_db.meta.sync_state import mark_stale_units

        client = MagicMock()
        client.command.return_value = 0
        mark_stale_units(client)

        first_call = client.command.call_args_list[0][0][0]
        assert "Asia/Shanghai" in first_call

    def test_insert_sets_partial_status(self):
        from tushare_db.meta.sync_state import mark_stale_units

        client = MagicMock()
        client.command.side_effect = [1, None]
        mark_stale_units(client)

        insert_call = client.command.call_args_list[1][0][0]
        assert "'partial'" in insert_call
        assert "'heartbeat timeout'" in insert_call


class TestCreateRun:
    """sync_runs.py — create_run."""

    def test_creates_run_with_running_status(self):
        from tushare_db.meta.sync_runs import create_run

        client = MagicMock()
        run_id = create_run(client, "stock_daily", "A", "daily", 10)

        assert run_id is not None
        client.insert.assert_called_once()

    def test_run_id_is_uuid(self):
        from tushare_db.meta.sync_runs import create_run
        client = MagicMock()
        run_id = create_run(client, "test", "B", "test", 1)
        uuid.UUID(str(run_id))


class TestUpdateRun:
    """sync_runs.py — update_run."""

    def test_update_done(self):
        from tushare_db.meta.sync_runs import update_run
        import uuid

        client = MagicMock()
        run_id = uuid.uuid4()
        update_run(client, run_id, units_done=5, status="done")

        sql = client.command.call_args[0][0]
        assert "units_done = 5" in sql
        assert "status = 'done'" in sql
        assert "finished_at" in sql

    def test_update_failed(self):
        from tushare_db.meta.sync_runs import update_run
        import uuid

        client = MagicMock()
        run_id = uuid.uuid4()
        update_run(client, run_id, units_failed=2, status="failed")

        sql = client.command.call_args[0][0]
        assert "units_failed = 2" in sql
        assert "status = 'failed'" in sql

    def test_update_partial(self):
        from tushare_db.meta.sync_runs import update_run
        import uuid

        client = MagicMock()
        run_id = uuid.uuid4()
        update_run(client, run_id, units_done=3, status="partial")

        sql = client.command.call_args[0][0]
        assert "status = 'partial'" in sql
        assert "finished_at" in sql

    def test_no_updates_returns_early(self):
        from tushare_db.meta.sync_runs import update_run
        import uuid

        client = MagicMock()
        run_id = uuid.uuid4()
        update_run(client, run_id)

        client.command.assert_not_called()

    def test_run_id_in_query(self):
        from tushare_db.meta.sync_runs import update_run
        import uuid

        client = MagicMock()
        run_id = uuid.uuid4()
        update_run(client, run_id, units_done=1)

        sql = client.command.call_args[0][0]
        assert str(run_id) in sql
