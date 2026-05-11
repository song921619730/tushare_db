"""Unit tests for B10 fix: backfill module extraction."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from tushare_db.runner.backfill import get_layer, select_specs, run_backfill


class TestGetLayer:
    """B10: Verify layer mapping logic."""

    def _spec(self, batch="A", priority="P0", strategy="date_loop", enabled=True):
        """Create a mock InterfaceSpec."""
        spec = MagicMock()
        spec.batch = batch
        spec.priority = priority
        spec.fetch_strategy = MagicMock()
        spec.fetch_strategy.kind = strategy
        spec.enabled = enabled
        spec.name = "test_interface"
        return spec

    def test_reference_is_layer_0(self):
        assert get_layer(self._spec(batch="reference")) == 0

    def test_daily_p0_is_layer_1(self):
        assert get_layer(self._spec(batch="A", priority="P0", strategy="date_loop")) == 1

    def test_paging_p0_is_layer_1(self):
        assert get_layer(self._spec(batch="A", priority="P0", strategy="offset_paging")) == 1

    def test_p1_non_period_is_layer_2(self):
        assert get_layer(self._spec(batch="B", priority="P1", strategy="date_loop")) == 2

    def test_period_loop_is_layer_3(self):
        assert get_layer(self._spec(batch="D", priority="P1", strategy="period_loop")) == 3

    def test_per_symbol_period_is_layer_3(self):
        assert get_layer(self._spec(batch="D", priority="P1", strategy="per_symbol_period")) == 3

    def test_p2_is_layer_4(self):
        assert get_layer(self._spec(batch="D", priority="P2", strategy="date_loop")) == 4

    def test_p3_is_layer_5(self):
        assert get_layer(self._spec(batch="D", priority="P3", strategy="date_loop")) == 5


class TestSelectSpecs:
    """B10: Verify spec selection logic."""

    @patch("tushare_db.runner.backfill.load_interface_specs")
    def test_select_by_interface(self, mock_load):
        s1 = MagicMock()
        s1.enabled = True
        s1.name = "daily"
        s2 = MagicMock()
        s2.enabled = True
        s2.name = "weekly"
        mock_load.return_value = [s1, s2]

        result = select_specs(interface="daily")
        assert len(result) == 1
        assert result[0].name == "daily"

    @patch("tushare_db.runner.backfill.load_interface_specs")
    def test_select_by_priority(self, mock_load):
        s1 = MagicMock(); s1.enabled = True; s1.priority = "P0"; s1.name = "daily"
        s2 = MagicMock(); s2.enabled = True; s2.priority = "P3"; s2.name = "macro"
        mock_load.return_value = [s1, s2]

        result = select_specs(priority="P0")
        assert len(result) == 1
        assert result[0].priority == "P0"

    @patch("tushare_db.runner.backfill.load_interface_specs")
    def test_select_default_p0_p1(self, mock_load):
        s1 = MagicMock(); s1.enabled = True; s1.priority = "P0"
        s2 = MagicMock(); s2.enabled = True; s2.priority = "P1"
        s3 = MagicMock(); s3.enabled = True; s3.priority = "P3"
        s4 = MagicMock(); s4.enabled = False; s4.priority = "P0"
        mock_load.return_value = [s1, s2, s3, s4]

        result = select_specs()
        assert len(result) == 2  # P0 + P1, enabled only


class TestRunBackfill:
    """B10: Verify backfill execution flow."""

    @patch("tushare_db.runner.backfill.plan_units")
    @patch("tushare_db.runner.backfill.execute_batch")
    def test_run_backfill_returns_summary(self, mock_exec, mock_plan):
        mock_spec = MagicMock()
        mock_spec.name = "daily"

        mock_plan.return_value = [MagicMock(scope_key="daily:20240102")]
        mock_exec.return_value = (1, 1, 0)  # total, done, failed

        mock_ch = MagicMock()
        mock_tushare = MagicMock()

        result = run_backfill(
            [mock_spec], mock_tushare, mock_ch,
            start_date="20240101", end_date="20240131",
        )

        assert result["total"] == 1
        assert result["done"] == 1
        assert result["failed"] == 0
        assert "run_id" in result

    @patch("tushare_db.runner.backfill.plan_units")
    def test_empty_units_skipped(self, mock_plan):
        mock_spec = MagicMock()
        mock_spec.name = "daily"
        mock_plan.return_value = []

        mock_ch = MagicMock()
        mock_tushare = MagicMock()

        result = run_backfill([mock_spec], mock_tushare, mock_ch)

        assert result["total"] == 0
        assert result["done"] == 0
        assert result["failed"] == 0
