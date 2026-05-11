"""Tests for bootstrap, dedupe, logging_setup, core/clock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBootstrap:
    """meta/bootstrap.py — _meta DDL and init."""

    def test_meta_tables_defined(self):
        from tushare_db.meta.bootstrap import META_TABLES_DDL

        assert "sync_state" in META_TABLES_DDL
        assert "sync_runs" in META_TABLES_DDL
        assert "api_calls" in META_TABLES_DDL

    def test_sync_state_ddl_has_replacing_merge_tree(self):
        from tushare_db.meta.bootstrap import META_TABLES_DDL

        ddl = META_TABLES_DDL["sync_state"]
        assert "ReplacingMergeTree" in ddl
        assert "_version" in ddl

    def test_sync_runs_ddl_has_uuid(self):
        from tushare_db.meta.bootstrap import META_TABLES_DDL

        ddl = META_TABLES_DDL["sync_runs"]
        assert "UUID" in ddl

    def test_api_calls_ddl_has_ttl(self):
        from tushare_db.meta.bootstrap import META_TABLES_DDL

        ddl = META_TABLES_DDL["api_calls"]
        assert "TTL" in ddl

    def test_init_meta_creates_database_and_tables(self):
        from tushare_db.meta.bootstrap import init_meta

        client = MagicMock()
        init_meta(client)

        # CREATE DATABASE + 3 CREATE TABLEs
        assert client.command.call_count == 4
        calls = [c[0][0] for c in client.command.call_args_list]
        assert "CREATE DATABASE IF NOT EXISTS _meta" in calls

    def test_init_tushare_db(self):
        from tushare_db.meta.bootstrap import init_tushare_db

        client = MagicMock()
        init_tushare_db(client)

        client.command.assert_called_once_with("CREATE DATABASE IF NOT EXISTS tushare")

    def test_verify_init_passes(self):
        from tushare_db.meta.bootstrap import verify_init

        client = MagicMock()
        client.command.return_value = "api_calls\nsync_runs\nsync_state"
        # Should not raise
        verify_init(client)

    def test_verify_init_fails_on_missing(self):
        from tushare_db.meta.bootstrap import verify_init

        client = MagicMock()
        client.command.return_value = "api_calls"  # Missing sync_runs, sync_state
        with pytest.raises(RuntimeError, match="Missing"):
            verify_init(client)


class TestDedupe:
    """sink/dedupe.py — deduplicate_table."""

    def test_deduplicate_table(self):
        from tushare_db.sink.dedupe import deduplicate_table

        client = MagicMock()
        deduplicate_table(client, "tushare_daily")

        client.command.assert_called_once()
        sql = client.command.call_args[0][0]
        assert "OPTIMIZE TABLE" in sql
        assert "FINAL" in sql
        assert "tushare.tushare_daily" in sql

    def test_deduplicate_custom_database(self):
        from tushare_db.sink.dedupe import deduplicate_table

        client = MagicMock()
        deduplicate_table(client, "_meta_sync_state", database="_meta")

        sql = client.command.call_args[0][0]
        assert "_meta._meta_sync_state" in sql


class TestLoggingSetup:
    """logging_setup.py — structlog dual handler."""

    def test_structlog_configured(self):
        """Verify structlog is configured without errors."""
        import structlog
        from tushare_db.logging_setup import setup_logging

        setup_logging()
        assert structlog.get_config() is not None

    def test_get_logger(self):
        """get_logger returns a working logger."""
        import structlog
        from tushare_db.logging_setup import setup_logging

        setup_logging()
        logger = structlog.get_logger(__name__)
        # Should not raise
        logger.info("test", foo="bar")


class TestCoreClock:
    """core/clock.py — Clock protocol and FakeClock."""

    def test_fake_clock_fixed_time(self):
        from tushare_db.core.clock import FakeClock
        from datetime import datetime

        clock = FakeClock(fixed=datetime(2024, 6, 15, 10, 0, 0))
        t = clock.now()
        assert t.year == 2024
        assert t.month == 6
        assert t.day == 15

    def test_fake_clock_advance(self):
        from tushare_db.core.clock import FakeClock
        from datetime import datetime

        clock = FakeClock(fixed=datetime(2024, 1, 1, 12, 0, 0))
        clock.advance(60)  # 1 minute
        t = clock.now()
        assert t.second == 0
        assert t.minute == 1

    def test_fake_clock_set(self):
        from tushare_db.core.clock import FakeClock
        from datetime import datetime

        clock = FakeClock()
        clock.advance(100)  # advance first
        new_time = datetime(2025, 1, 1, 0, 0, 0)
        clock.set(new_time)
        assert clock.now() == new_time

    def test_system_clock_now(self):
        """SystemClock returns real time."""
        from tushare_db.core.clock import SystemClock
        from datetime import datetime

        clock = SystemClock()
        t = clock.now()
        assert isinstance(t, datetime)
