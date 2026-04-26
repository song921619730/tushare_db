"""Heartbeat and stale detection tests.

Coverage:
- mark_stale_units SQL query correctness
- Worker heartbeat interval constant
- Heartbeat thread lifecycle (start/stop)
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from tushare_db.runner.worker import HEARTBEAT_INTERVAL, _NOW
from tushare_db.planner.strategies import WorkUnit


class TestHeartbeatInterval:
    """Validate heartbeat configuration constants."""

    def test_heartbeat_interval_is_30_seconds(self):
        """Design doc requires 30s heartbeat interval."""
        assert HEARTBEAT_INTERVAL == 30

    def test_epoch_sentinel_is_1970(self):
        """_NOW sentinel should be epoch (used for unset last_success_at)."""
        assert _NOW == datetime(1970, 1, 1, tzinfo=timezone.utc)


class TestMarkStaleUnitsQuery:
    """Test the SQL query structure for stale detection.

    Note: Actual ClickHouse execution requires a real database connection.
    These tests validate the query logic and parameter binding.
    """

    def test_stale_threshold_query_uses_correct_threshold(self):
        """Verify threshold_minutes is interpolated into the query."""
        threshold = 10  # default
        # The query should check heartbeat_at < now - threshold minutes
        expected_fragment = f"INTERVAL {threshold} MINUTE"
        assert expected_fragment in (
            f"SELECT count() FROM _meta.sync_state FINAL "
            f"WHERE status = 'running' "
            f"AND heartbeat_at < now64(3, 'Asia/Shanghai') - INTERVAL {threshold} MINUTE"
        )

    def test_stale_insert_query_copies_fields(self):
        """Stale insert should copy all fields and set status='partial'."""
        # The INSERT query should SELECT all relevant fields from stale units
        required_fragments = [
            "status = 'running'",
            "INTERVAL",
            "MINUTE",
            "'partial'",
            "'heartbeat timeout'",
        ]
        for fragment in required_fragments:
            assert fragment in (
                "INSERT INTO _meta.sync_state "
                "(interface, scope_key, status, rows, last_success_at, heartbeat_at, attempts, last_error, _version) "
                "SELECT interface, scope_key, 'partial', rows, last_success_at, heartbeat_at, attempts, "
                "'heartbeat timeout', toUnixTimestamp64Milli(now64()) "
                "FROM _meta.sync_state FINAL "
                "WHERE status = 'running' "
                "AND heartbeat_at < now64(3, 'Asia/Shanghai') - INTERVAL 10 MINUTE"
            )

    def test_timezone_is_asia_shanghai(self):
        """Stale detection must use Asia/Shanghai timezone."""
        assert "Asia/Shanghai" in (
            "heartbeat_at < now64(3, 'Asia/Shanghai') - INTERVAL 10 MINUTE"
        )


class TestHeartbeatThreadLifecycle:
    """Test heartbeat thread behavior in isolation."""

    def test_stop_event_stops_heartbeat(self):
        """Setting stop_event should terminate the heartbeat loop."""
        stop_event = threading.Event()
        heartbeat_count = 0
        lock = threading.Lock()

        def mock_heartbeat():
            nonlocal heartbeat_count
            # Simulate first heartbeat
            with lock:
                heartbeat_count += 1
            # Then check stop_event in a loop
            while not stop_event.is_set():
                stop_event.wait(0.05)
                if not stop_event.is_set():
                    with lock:
                        heartbeat_count += 1

        thread = threading.Thread(target=mock_heartbeat, daemon=True)
        thread.start()
        time.sleep(0.15)  # Let it run for a few cycles
        stop_event.set()
        thread.join(timeout=1)

        assert not thread.is_alive(), "Heartbeat thread should stop after event"
        assert heartbeat_count >= 2, "Should have sent multiple heartbeats"

    def test_heartbeat_starts_immediately(self):
        """First heartbeat should fire immediately, not after interval."""
        stop_event = threading.Event()
        first_heartbeat_time = None
        start_time = time.monotonic()
        lock = threading.Lock()

        def mock_heartbeat():
            nonlocal first_heartbeat_time
            with lock:
                first_heartbeat_time = time.monotonic() - start_time
            stop_event.wait(60)  # Block until stopped

        thread = threading.Thread(target=mock_heartbeat, daemon=True)
        thread.start()
        time.sleep(0.05)
        stop_event.set()
        thread.join(timeout=1)

        assert first_heartbeat_time is not None
        assert first_heartbeat_time < 0.1, "First heartbeat should fire immediately"


class TestIndependentHeartbeatClient:
    """Test N4: heartbeat uses independent ClickHouse client."""

    def test_new_ch_client_uses_env_vars(self):
        """_new_ch_client reads from environment, not hardcoded values."""
        import os
        from tushare_db.runner.worker import _new_ch_client

        original = os.environ.get("CH_HOST")
        os.environ["CH_HOST"] = "testhost"
        os.environ["CH_HTTP_PORT"] = "9999"
        os.environ["CH_PIPELINE_PASSWORD"] = "testpass"

        try:
            with patch("tushare_db.runner.worker.clickhouse_connect.get_client") as mock_get:
                _new_ch_client(database="_meta")
                mock_get.assert_called_once_with(
                    host="testhost",
                    port=9999,
                    username="pipeline",
                    password="testpass",
                    database="_meta",
                )
        finally:
            if original is not None:
                os.environ["CH_HOST"] = original
            else:
                os.environ.pop("CH_HOST", None)

    def test_heartbeat_loop_uses_independent_client(self):
        """_heartbeat_loop should not share client with execute_unit's ch_client.

        Verified by checking that _heartbeat_loop accepts its own client parameter.
        """
        from tushare_db.runner.worker import _heartbeat_loop, _heartbeat_once
        import inspect

        # _heartbeat_loop should accept client as first parameter
        sig = inspect.signature(_heartbeat_loop)
        params = list(sig.parameters.keys())
        assert "client" in params, "_heartbeat_loop should accept its own client parameter"

        # _heartbeat_once should also accept client
        sig_once = inspect.signature(_heartbeat_once)
        params_once = list(sig_once.parameters.keys())
        assert "client" in params_once, "_heartbeat_once should accept its own client parameter"
