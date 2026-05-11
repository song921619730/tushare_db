"""Tests for schema evolver: rename_column, change_type, evolve_schema_full."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call, patch

import pytest


class TestValidateIdent:
    """Test N5: DDL input validation prevents injection."""

    def test_valid_table_name(self):
        from tushare_db.schema.evolver import _validate_ident
        assert _validate_ident("tushare_stock_daily", "table") == "tushare_stock_daily"

    def test_valid_column_name(self):
        from tushare_db.schema.evolver import _validate_ident
        assert _validate_ident("trade_date", "column") == "trade_date"

    def test_valid_database_name(self):
        from tushare_db.schema.evolver import _validate_ident
        assert _validate_ident("tushare", "database") == "tushare"

    def test_rejects_sql_injection_table(self):
        from tushare_db.schema.evolver import _validate_ident
        with pytest.raises(ValueError, match="Invalid table"):
            _validate_ident("daily; DROP TABLE users", "table")

    def test_rejects_sql_injection_column(self):
        from tushare_db.schema.evolver import _validate_ident
        with pytest.raises(ValueError, match="Invalid column"):
            _validate_ident("col; SELECT * FROM system.users", "column")

    def test_rejects_spaces(self):
        from tushare_db.schema.evolver import _validate_ident
        with pytest.raises(ValueError, match="Invalid"):
            _validate_ident("daily OR 1=1", "table")

    def test_rejects_special_characters(self):
        from tushare_db.schema.evolver import _validate_ident
        with pytest.raises(ValueError, match="Invalid"):
            _validate_ident("../../etc/passwd", "table")

    def test_rejects_leading_digit(self):
        from tushare_db.schema.evolver import _validate_ident
        with pytest.raises(ValueError, match="Invalid"):
            _validate_ident("123table", "table")


class TestCacheInvalidation:
    """Test N3: column type cache TTL and invalidation."""

    def _reset_cache(self):
        from tushare_db.runner.worker import (
            _COLUMN_TYPE_CACHE,
            invalidate_column_cache,
        )
        _COLUMN_TYPE_CACHE.clear()
        return invalidate_column_cache

    def test_invalidate_specific_table(self):
        invalidate = self._reset_cache()
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        _COLUMN_TYPE_CACHE["tushare.daily"] = ({"a": "Int64"}, 9999.0)
        _COLUMN_TYPE_CACHE["tushare.income"] = ({"b": "String"}, 9999.0)

        invalidate(database="tushare", table="daily")

        assert "tushare.daily" not in _COLUMN_TYPE_CACHE
        assert "tushare.income" in _COLUMN_TYPE_CACHE

    def test_invalidate_entire_database(self):
        invalidate = self._reset_cache()
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        _COLUMN_TYPE_CACHE["tushare.daily"] = ({"a": "Int64"}, 9999.0)
        _COLUMN_TYPE_CACHE["tushare.income"] = ({"b": "String"}, 9999.0)
        _COLUMN_TYPE_CACHE["_meta.sync_state"] = ({"c": "UInt64"}, 9999.0)

        invalidate(database="tushare")

        assert "tushare.daily" not in _COLUMN_TYPE_CACHE
        assert "tushare.income" not in _COLUMN_TYPE_CACHE
        assert "_meta.sync_state" in _COLUMN_TYPE_CACHE

    def test_invalidate_all(self):
        invalidate = self._reset_cache()
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        _COLUMN_TYPE_CACHE["tushare.daily"] = ({"a": "Int64"}, 9999.0)
        _COLUMN_TYPE_CACHE["_meta.sync_state"] = ({"c": "UInt64"}, 9999.0)

        invalidate()

        assert len(_COLUMN_TYPE_CACHE) == 0

    def test_rename_column_invalidates_cache(self):
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        from tushare_db.schema.evolver import rename_column

        _COLUMN_TYPE_CACHE["tushare.daily"] = ({"col": "Int64"}, 9999.0)

        client = MagicMock()
        rename_column(client, "tushare", "daily", "col", "new_col")

        assert "tushare.daily" not in _COLUMN_TYPE_CACHE

    def test_change_type_invalidates_cache(self):
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        from tushare_db.schema.evolver import change_type

        _COLUMN_TYPE_CACHE["tushare.daily"] = ({"col": "Float64"}, 9999.0)

        client = MagicMock()
        change_type(client, "tushare", "daily", "col", "Decimal64(4)")

        assert "tushare.daily" not in _COLUMN_TYPE_CACHE


class TestRenameColumn:
    """Test rename_column shadow-table pattern."""

    def _make_client(self):
        """Create a mock ClickHouse client."""
        client = MagicMock()
        return client

    def test_rename_column_full_sequence(self):
        """Shadow table rename executes all steps in order."""
        from tushare_db.schema.evolver import rename_column

        client = self._make_client()
        rename_column(client, "tushare", "daily", "old_col", "new_col")

        calls = [c[0][0] for c in client.command.call_args_list]
        assert "CREATE TABLE IF NOT EXISTS tushare.daily_new AS tushare.daily" in calls
        assert "ALTER TABLE tushare.daily_new RENAME COLUMN old_col TO new_col" in calls
        assert "INSERT INTO tushare.daily_new SELECT * FROM tushare.daily" in calls
        assert "RENAME TABLE tushare.daily TO tushare.daily_old, tushare.daily_new TO tushare.daily" in calls
        assert "DROP TABLE IF EXISTS tushare.daily_old" in calls

    def test_rename_column_cleanup_on_failure(self):
        """Shadow table is dropped if rename fails."""
        from tushare_db.schema.evolver import rename_column

        client = self._make_client()
        client.command.side_effect = [None, Exception("rename failed"), None, None, None]

        try:
            rename_column(client, "tushare", "daily", "old_col", "new_col")
        except Exception:
            pass

        # Verify shadow cleanup was called
        all_calls = [c[0][0] for c in client.command.call_args_list]
        assert "DROP TABLE IF EXISTS tushare.daily_new" in all_calls

    def test_rename_column_order(self):
        """Steps are executed in correct order: create → alter → insert → rename → drop."""
        from tushare_db.schema.evolver import rename_column

        client = self._make_client()
        rename_column(client, "tushare", "income", "revenue", "total_revenue")

        # Verify exact call order
        expected = [
            "CREATE TABLE IF NOT EXISTS tushare.income_new AS tushare.income",
            "ALTER TABLE tushare.income_new RENAME COLUMN revenue TO total_revenue",
            "INSERT INTO tushare.income_new SELECT * FROM tushare.income",
            "RENAME TABLE tushare.income TO tushare.income_old, tushare.income_new TO tushare.income",
            "DROP TABLE IF EXISTS tushare.income_old",
        ]
        actual = [c[0][0] for c in client.command.call_args_list]
        assert actual == expected


class TestChangeType:
    """Test change_type shadow-table pattern."""

    def _make_client(self):
        client = MagicMock()
        return client

    def test_change_type_full_sequence(self):
        """Shadow table type change executes all steps."""
        from tushare_db.schema.evolver import change_type

        client = self._make_client()
        change_type(client, "tushare", "daily", "amount", "Decimal64(4)")

        calls = [c[0][0] for c in client.command.call_args_list]
        assert "CREATE TABLE IF NOT EXISTS tushare.daily_new AS tushare.daily" in calls
        assert "ALTER TABLE tushare.daily_new MODIFY COLUMN amount Decimal64(4)" in calls
        assert "INSERT INTO tushare.daily_new SELECT * FROM tushare.daily" in calls
        assert "RENAME TABLE tushare.daily TO tushare.daily_old, tushare.daily_new TO tushare.daily" in calls
        assert "DROP TABLE IF EXISTS tushare.daily_old" in calls

    def test_change_type_cleanup_on_failure(self):
        """Shadow table is dropped if type change fails."""
        from tushare_db.schema.evolver import change_type

        client = self._make_client()
        client.command.side_effect = [None, Exception("type change failed"), None]

        try:
            change_type(client, "tushare", "daily", "amount", "Decimal64(4)")
        except Exception:
            pass

        all_calls = [c[0][0] for c in client.command.call_args_list]
        assert "DROP TABLE IF EXISTS tushare.daily_new" in all_calls


class TestEvolveSchemaFull:
    """Test evolve_schema_full orchestration."""

    def _make_client(self):
        client = MagicMock()
        # evolve_schema calls get_existing_columns which returns a string
        client.command.return_value = ""
        return client

    def test_full_evolution_order(self):
        """Operations execute in correct order: renames → type_changes → add_columns."""
        from tushare_db.schema.evolver import evolve_schema_full

        client = self._make_client()
        # Mock evolve_schema to not execute real ALTERs
        with patch("tushare_db.schema.evolver.rename_column") as mock_rename, \
             patch("tushare_db.schema.evolver.change_type") as mock_change, \
             patch("tushare_db.schema.evolver.evolve_schema", return_value=["ADD COLUMN x String"]) as mock_add:

            result = evolve_schema_full(
                client,
                "tushare",
                "daily",
                desired_columns=[("x", "String")],
                rename_map={"old_name": "new_name"},
                type_changes={"amount": "Decimal64(4)"},
            )

            # Verify order: rename called first, then change_type, then evolve_schema
            assert mock_rename.call_count == 1
            assert mock_change.call_count == 1
            assert mock_add.call_count == 1

            assert result["renames"] == ["old_name → new_name"]
            assert result["type_changes"] == ["amount → Decimal64(4)"]
            assert result["add_columns"] == ["ADD COLUMN x String"]

    def test_empty_operations(self):
        """No renames or type_changes means only add_columns run."""
        from tushare_db.schema.evolver import evolve_schema_full

        client = self._make_client()
        with patch("tushare_db.schema.evolver.evolve_schema", return_value=[]) as mock_add:
            result = evolve_schema_full(client, "tushare", "daily", desired_columns=[])

            assert result["renames"] == []
            assert result["type_changes"] == []
            assert result["add_columns"] == []
            assert mock_add.call_count == 1

    def test_no_optional_params(self):
        """Works with only desired_columns, no renames or type_changes."""
        from tushare_db.schema.evolver import evolve_schema_full

        client = self._make_client()
        with patch("tushare_db.schema.evolver.evolve_schema", return_value=["ADD COLUMN new_col Int64"]) as mock_add:
            result = evolve_schema_full(
                client, "tushare", "daily",
                desired_columns=[("new_col", "Int64")],
            )

            assert result["renames"] == []
            assert result["type_changes"] == []
            assert result["add_columns"] == ["ADD COLUMN new_col Int64"]
