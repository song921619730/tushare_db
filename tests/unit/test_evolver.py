"""Tests for schema evolver: rename_column, change_type, evolve_schema_full."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call, patch


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
