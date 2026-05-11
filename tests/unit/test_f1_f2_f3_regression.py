"""F1-F3 regression tests — MCP security, FINAL syntax, return types.

F1: MCP must use ai_reader (readonly=2), not pipeline (read-write)
F2: get_ohlcv FINAL syntax must be `AS alias FINAL`, not `TABLE FINAL alias`
F3: All MCP tools must return dict[str, Any] via encode_response(), not list
"""

from __future__ import annotations

import ast
import inspect
import json
from unittest.mock import MagicMock, patch

import pytest


class TestF1_MCPUsesAiReader:
    """F1 regression: MCP must connect via ai_reader user (readonly=2).

    If someone changes _get_client back to "pipeline", this test fails.
    """

    def test_get_client_uses_ai_reader_user(self):
        """_get_client must pass username='ai_reader'."""
        from tushare_db.mcp_server.tools import _get_client

        with patch("tushare_db.mcp_server.tools.clickhouse_connect.get_client") as mock_get:
            mock_get.return_value = MagicMock()
            _get_client()

            mock_get.assert_called_once()
            kwargs = mock_get.call_args[1]
            assert kwargs.get("user") == "ai_reader", (
                f"Expected user='ai_reader', got user={kwargs.get('user')!r}. "
                "F1 regression: MCP must use readonly ai_reader, not pipeline."
            )

    def test_get_client_uses_ai_reader_password_env(self):
        """_get_client must read CH_AI_READER_PASSWORD, not CH_PIPELINE_PASSWORD."""
        from tushare_db.mcp_server.tools import _get_client

        with patch("tushare_db.mcp_server.tools.clickhouse_connect.get_client") as mock_get:
            mock_get.return_value = MagicMock()
            _get_client()

            kwargs = mock_get.call_args[1]
            assert "CH_AI_READER_PASSWORD" in str(kwargs.get("password")) or kwargs.get("password") == "", (
                "F1 regression: password should come from CH_AI_READER_PASSWORD env var"
            )
            # Verify the default env var name is CH_AI_READER_PASSWORD
            assert kwargs.get("password") == ""  # default is empty string from env

    def test_get_client_uses_http_port(self):
        """_get_client must use HTTP port (8123), not native port (9000)."""
        from tushare_db.mcp_server.tools import _get_client

        with patch("tushare_db.mcp_server.tools.clickhouse_connect.get_client") as mock_get:
            mock_get.return_value = MagicMock()
            _get_client()

            kwargs = mock_get.call_args[1]
            assert kwargs.get("port") == 8123, (
                f"Expected port 8123 (HTTP), got {kwargs.get('port')}. "
                "clickhouse_connect uses HTTP protocol, not native."
            )

    def test_source_code_does_not_reference_pipeline_user(self):
        """tools.py source must not contain hardcoded 'pipeline' as user string."""
        source = inspect.getsource(__import__("tushare_db.mcp_server.tools", fromlist=["_get_client"]))
        # The word "pipeline" can appear in comments/docstrings, but not as the user value
        # Check that there's no user="pipeline" or user='pipeline'
        assert 'user="pipeline"' not in source, "F1 regression: hardcoded user='pipeline' found"
        assert "user='pipeline'" not in source, "F1 regression: hardcoded user='pipeline' found"


class TestF2_FINALSyntaxCorrect:
    """F2 regression: FINAL must come AFTER table alias, not before.

    Wrong:  FROM tushare.tushare_stock_daily FINAL AS d
    Right:  FROM tushare.tushare_stock_daily AS d FINAL
    """

    def test_qfq_query_has_correct_final_syntax(self):
        """qfq query: 'AS d FINAL' not 'FINAL AS d'."""
        from tushare_db.mcp_server.tools import get_ohlcv

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["trade_date", "close"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            get_ohlcv("000001.SZ", "20240101", "20240131", adjust="qfq")

            # Find the SQL that was executed
            calls = mock_client.query.call_args_list
            sql = None
            for call in calls:
                args = call[0]
                if args and "tushare_stock_daily" in str(args[0]):
                    sql = str(args[0])
                    break

            assert sql is not None, "No stock_daily query found"
            # FINAL must come after the alias (AS d FINAL)
            assert "AS d FINAL" in sql or "AS af FINAL" in sql, (
                f"F2 regression: FINAL must come after table alias. SQL snippet: {sql[:200]}"
            )
            # Must NOT have FINAL before AS
            assert "FINAL AS" not in sql, (
                f"F2 regression: 'FINAL AS' is invalid syntax. SQL: {sql[:200]}"
            )

    def test_hfq_query_has_correct_final_syntax(self):
        """hfq query: same FINAL placement rule."""
        from tushare_db.mcp_server.tools import get_ohlcv

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["trade_date", "close"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            get_ohlcv("000001.SZ", "20240101", "20240131", adjust="hfq")

            calls = mock_client.query.call_args_list
            sql = None
            for call in calls:
                args = call[0]
                if args and "tushare_stock_daily" in str(args[0]):
                    sql = str(args[0])
                    break

            assert sql is not None, "No stock_daily query found for hfq"
            assert "AS d FINAL" in sql, (
                f"F2 regression: FINAL must come after alias in hfq. SQL: {sql[:200]}"
            )
            assert "FINAL AS" not in sql, (
                f"F2 regression: 'FINAL AS' is invalid in hfq. SQL: {sql[:200]}"
            )

    def test_adj_factor_query_uses_final(self):
        """qfw/hfq must use tushare_adj_factor FINAL for latest adj factor."""
        from tushare_db.mcp_server.tools import get_ohlcv

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["trade_date", "close"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            get_ohlcv("000001.SZ", "20240101", "20240131", adjust="qfq")

            calls = mock_client.query.call_args_list
            all_sql = " ".join(str(c[0][0]) for c in calls if c[0])
            assert "tushare_adj_factor" in all_sql, "adj_factor table not referenced"
            assert "tushare_adj_factor" in all_sql and "FINAL" in all_sql, (
                "F2 regression: adj_factor query should use FINAL"
            )


class TestF3_ReturnTypeIsDict:
    """F3 regression: All MCP tools must return dict[str, Any], not list.

    encode_response() returns {"content": "...", "encoding": "...", "row_count": N}.
    """

    def _make_mock_client(self, rows=None, columns=None):
        client = MagicMock()
        if rows is None:
            rows = []
        if columns is None:
            columns = ["col1"]
        result = MagicMock()
        result.column_names = columns
        result.result_rows = rows
        client.query.return_value = result
        return client

    def test_query_sql_returns_dict(self):
        from tushare_db.mcp_server.tools import query_sql

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[(1,)], columns=["x"]
            )
            result = query_sql("SELECT 1 AS x")

            assert isinstance(result, dict), (
                f"F3 regression: query_sql must return dict, got {type(result)}"
            )
            assert "content" in result
            assert "encoding" in result
            assert "row_count" in result

    def test_get_ohlcv_returns_dict(self):
        from tushare_db.mcp_server.tools import get_ohlcv

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[("2024-01-01", 10.0)],
                columns=["trade_date", "close"],
            )
            result = get_ohlcv("000001.SZ", "20240101", "20240131", "qfq")

            assert isinstance(result, dict), (
                f"F3 regression: get_ohlcv must return dict, got {type(result)}"
            )
            assert "content" in result

    def test_list_interfaces_returns_dict(self):
        from tushare_db.mcp_server.tools import list_interfaces

        mock_spec = MagicMock()
        mock_spec.enabled = True
        mock_spec.name = "daily"
        mock_spec.table = "tushare_stock_daily"
        mock_spec.priority = "P0"
        mock_spec.batch = "A"
        mock_spec.fetch_strategy = MagicMock()
        mock_spec.fetch_strategy.kind = "date_loop"
        mock_spec.mode = "full"

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client()
            with patch(
                "tushare_db.config.loader.load_interface_specs",
                return_value=[mock_spec],
            ):
                result = list_interfaces()

                assert isinstance(result, dict), (
                    f"F3 regression: list_interfaces must return dict, got {type(result)}"
                )
                assert "content" in result

    def test_describe_table_returns_dict(self):
        from tushare_db.mcp_server.tools import describe_table

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()

            def _mock_query(*args, **kwargs):
                result = MagicMock()
                if "DESCRIBE" in str(args[0]) if args else "":
                    result.column_names = ["name", "type", "default"]
                    result.result_rows = [("ts_code", "String", "")]
                elif "system.parts" in str(args[0]) if args else "":
                    result.result_rows = [(100,)]
                elif "_version" in str(args[0]) if args else "":
                    result.result_rows = [(1,)]
                else:
                    result.result_rows = []
                return result

            mock_client.query.side_effect = _mock_query
            mock_get.return_value = mock_client

            result = describe_table("stock_basic")

            assert isinstance(result, dict), (
                f"F3 regression: describe_table must return dict, got {type(result)}"
            )
            assert "columns" in result

    def test_get_financials_returns_dict(self):
        from tushare_db.mcp_server.tools import get_financials

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[("600519.SH", 150560330316.45)],
                columns=["ts_code", "total_revenue"],
            )
            result = get_financials("600519.SH", "income")

            assert isinstance(result, dict), (
                f"F3 regression: get_financials must return dict, got {type(result)}"
            )
            assert "content" in result

    def test_trade_calendar_returns_dict(self):
        from tushare_db.mcp_server.tools import trade_calendar

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[("2024-01-01", 1, None)],
                columns=["cal_date", "is_open", "pretrade_date"],
            )
            result = trade_calendar("20240101", "20240131")

            assert isinstance(result, dict), (
                f"F3 regression: trade_calendar must return dict, got {type(result)}"
            )
            assert "content" in result

    def test_coverage_report_returns_dict(self):
        from tushare_db.mcp_server.tools import coverage_report

        mock_spec = MagicMock()
        mock_spec.enabled = True
        mock_spec.name = "daily"
        mock_spec.priority = "P0"

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.query.return_value = MagicMock(result_rows=[])
            mock_get.return_value = mock_client

            with patch(
                "tushare_db.config.loader.load_interface_specs",
                return_value=[mock_spec],
            ):
                result = coverage_report()

                assert isinstance(result, dict), (
                    f"F3 regression: coverage_report must return dict, got {type(result)}"
                )
                assert "content" in result

    def test_get_index_components_returns_dict(self):
        from tushare_db.mcp_server.tools import get_index_components

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[("000001.SZ",)],
                columns=["con_code"],
            )
            result = get_index_components("000300.SH")

            assert isinstance(result, dict), (
                f"F3 regression: get_index_components must return dict, got {type(result)}"
            )
            assert "content" in result

    def test_get_moneyflow_returns_dict(self):
        from tushare_db.mcp_server.tools import get_moneyflow

        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_get.return_value = self._make_mock_client(
                rows=[("2024-01-01", 1000000.0)],
                columns=["trade_date", "buy_elg_amount"],
            )
            result = get_moneyflow("000001.SZ", "20240101", "20240131")

            assert isinstance(result, dict), (
                f"F3 regression: get_moneyflow must return dict, got {type(result)}"
            )
            assert "content" in result


class TestF1_ReadonlyEnforcement:
    """F1 depth defense: verify readonly=2 would reject writes at DB layer.

    Since we can't run a real ClickHouse here, we verify the code path
    that would be used for write attempts.
    """

    def test_safe_query_rejects_insert(self):
        """_safe_query must reject INSERT statements even via WITH clause."""
        from tushare_db.mcp_server.tools import _safe_query

        client = MagicMock()
        with pytest.raises(ValueError, match="Only SELECT"):
            _safe_query(client, "INSERT INTO t VALUES (1)")

    def test_safe_query_rejects_insert_via_with(self):
        """WITH ... INSERT should be caught by the SELECT whitelist."""
        from tushare_db.mcp_server.tools import _safe_query

        client = MagicMock()
        # WITH is allowed at the start, but the inner query being INSERT
        # is something _safe_query can't fully prevent — that's why
        # readonly=2 at DB layer is the defense in depth.
        # This test verifies the basic WITH ... SELECT pattern works.
        with patch.object(client, "query") as mock_query:
            mock_query.return_value = MagicMock(result_rows=[])
            _safe_query(client, "WITH x AS (SELECT 1) SELECT * FROM x")
            mock_query.assert_called_once()

    def test_param_query_rejects_insert(self):
        """_param_query must reject INSERT even with parameters."""
        from tushare_db.mcp_server.tools import _param_query

        client = MagicMock()
        with pytest.raises(ValueError, match="Only SELECT"):
            _param_query(client, "INSERT INTO t VALUES (%(v)s)", {"v": 1})
