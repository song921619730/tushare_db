"""MCP tools unit tests (mock ClickHouse).

Covers: input validation, query building, error handling, encoding.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from tushare_db.mcp_server.tools import (
    _validate_ts_code,
    _validate_date,
    _validate_exchange,
    _validate_statement,
    _SELECT_RE,
)


class TestValidateTsCode:
    """N2: ts_code whitelist validation."""

    def test_valid_sz(self):
        assert _validate_ts_code("000001.SZ") == "000001.SZ"

    def test_valid_sh(self):
        assert _validate_ts_code("600519.SH") == "600519.SH"

    def test_valid_bj(self):
        assert _validate_ts_code("830799.BJ") == "830799.BJ"

    def test_rejects_missing_dot(self):
        with pytest.raises(ValueError, match="Invalid ts_code"):
            _validate_ts_code("000001")

    def test_rejects_wrong_exchange(self):
        with pytest.raises(ValueError, match="Invalid ts_code"):
            _validate_ts_code("000001.NY")

    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="Invalid ts_code"):
            _validate_ts_code("001.SZ")

    def test_rejects_sqli_injection(self):
        """N2: SQLi in ts_code should be rejected."""
        with pytest.raises(ValueError, match="Invalid ts_code"):
            _validate_ts_code("000001.SZ; DROP TABLE users")

    def test_rejects_lowercase_exchange(self):
        with pytest.raises(ValueError, match="Invalid ts_code"):
            _validate_ts_code("000001.sz")


class TestValidateDate:
    """N2: date format validation."""

    def test_valid_date(self):
        assert _validate_date("20240101", "start_date") == "20240101"

    def test_valid_date_custom_name(self):
        assert _validate_date("20231231", "period") == "20231231"

    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="Invalid"):
            _validate_date("2024010")

    def test_rejects_non_digits(self):
        with pytest.raises(ValueError, match="Invalid"):
            _validate_date("2024-01-01")

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Invalid"):
            _validate_date("")


class TestValidateExchange:
    """N2: exchange whitelist validation."""

    @pytest.mark.parametrize("ex", ["SSE", "SZSE", "BSE", "CFFEX", "SHFE", "DCE", "CZCE"])
    def test_valid_exchanges(self, ex):
        assert _validate_exchange(ex) == ex

    def test_rejects_invalid_exchange(self):
        with pytest.raises(ValueError, match="Invalid exchange"):
            _validate_exchange("NYSE")

    def test_rejects_sqli_exchange(self):
        with pytest.raises(ValueError, match="Invalid exchange"):
            _validate_exchange("SSE; DROP TABLE users")


class TestValidateStatement:
    """N2: financial statement whitelist."""

    @pytest.mark.parametrize("stmt", ["income", "balancesheet", "cashflow", "fina_indicator"])
    def test_valid_statements(self, stmt):
        assert _validate_statement(stmt) == stmt

    def test_rejects_invalid_statement(self):
        with pytest.raises(ValueError, match="Unknown statement"):
            _validate_statement("users")

    def test_rejects_sqli_statement(self):
        with pytest.raises(ValueError, match="Unknown statement"):
            _validate_statement("income; DROP TABLE users")


class TestSelectReWhitelist:
    """N2: query_sql only allows SELECT/WITH/SHOW/DESCRIBE."""

    def test_select_allowed(self):
        assert _SELECT_RE.match("SELECT * FROM table")

    def test_with_allowed(self):
        assert _SELECT_RE.match("WITH cte AS (SELECT 1) SELECT * FROM cte")

    def test_show_allowed(self):
        assert _SELECT_RE.match("SHOW TABLES")

    def test_describe_allowed(self):
        assert _SELECT_RE.match("DESCRIBE table")

    def test_describe_lowercase(self):
        assert _SELECT_RE.match("describe table")

    def test_insert_rejected(self):
        assert not _SELECT_RE.match("INSERT INTO table")

    def test_delete_rejected(self):
        assert not _SELECT_RE.match("DELETE FROM table")

    def test_update_rejected(self):
        assert not _SELECT_RE.match("UPDATE table SET x=1")

    def test_drop_rejected(self):
        assert not _SELECT_RE.match("DROP TABLE users")


class TestQuerySql:
    """MCP query_sql tool unit tests."""

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

    def test_query_returns_rows(self):
        from tushare_db.mcp_server.tools import _safe_query, _rows_to_dicts

        client = self._make_mock_client(
            rows=[("a", 1), ("b", 2)],
            columns=["name", "value"],
        )
        result = _safe_query(client, "SELECT name, value FROM t")

        assert len(result) == 2
        assert result[0] == {"name": "a", "value": 1}
        assert result[1] == {"name": "b", "value": 2}

    def test_query_rejects_insert(self):
        from tushare_db.mcp_server.tools import _safe_query

        client = self._make_mock_client()
        with pytest.raises(ValueError, match="Only SELECT"):
            _safe_query(client, "INSERT INTO t VALUES (1)")

    def test_query_rejects_delete(self):
        from tushare_db.mcp_server.tools import _safe_query

        client = self._make_mock_client()
        with pytest.raises(ValueError, match="Only SELECT"):
            _safe_query(client, "DELETE FROM t WHERE 1=1")

    def test_rows_to_dicts_handles_date(self):
        from tushare_db.mcp_server.tools import _rows_to_dicts
        from datetime import date

        result = MagicMock()
        result.column_names = ["trade_date"]
        result.result_rows = [(date(2024, 1, 1),)]

        rows = _rows_to_dicts(result)
        assert rows[0]["trade_date"] == "2024-01-01"

    def test_rows_to_dicts_handles_none(self):
        from tushare_db.mcp_server.tools import _rows_to_dicts

        result = MagicMock()
        result.column_names = ["a", "b"]
        result.result_rows = [(1, None), (None, 2)]

        rows = _rows_to_dicts(result)
        assert rows[0] == {"a": 1, "b": None}
        assert rows[1] == {"a": None, "b": 2}

    def test_rows_to_dicts_short_row(self):
        """Row with fewer values than columns should not crash."""
        from tushare_db.mcp_server.tools import _rows_to_dicts

        result = MagicMock()
        result.column_names = ["a", "b", "c"]
        result.result_rows = [(1,)]

        rows = _rows_to_dicts(result)
        assert rows[0] == {"a": 1, "b": None, "c": None}


class TestGetOhlcvValidation:
    """get_ohlcv input validation (no DB needed for validation tests)."""

    def test_rejects_bad_ts_code(self):
        from tushare_db.mcp_server.tools import get_ohlcv

        with pytest.raises(ValueError, match="Invalid ts_code"):
            get_ohlcv("bad", "20240101", "20240131")

    def test_rejects_bad_start_date(self):
        with pytest.raises(ValueError, match="Invalid start_date"):
            from tushare_db.mcp_server.tools import get_ohlcv
            get_ohlcv("000001.SZ", "2024-01-01", "20240131")

    def test_rejects_bad_end_date(self):
        with pytest.raises(ValueError, match="Invalid end_date"):
            from tushare_db.mcp_server.tools import get_ohlcv
            get_ohlcv("000001.SZ", "20240101", "bad")

    def test_rejects_invalid_adjust(self):
        with pytest.raises(ValueError, match="adjust must be"):
            from tushare_db.mcp_server.tools import get_ohlcv
            get_ohlcv("000001.SZ", "20240101", "20240131", adjust="invalid")

    def test_accepts_qfq(self):
        from tushare_db.mcp_server.tools import get_ohlcv
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["trade_date", "close"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            result = get_ohlcv("000001.SZ", "20240101", "20240131", adjust="qfq")
            assert "content" in result
            assert "encoding" in result


class TestGetFinancialsValidation:
    """get_financials input validation."""

    def test_rejects_bad_ts_code(self):
        from tushare_db.mcp_server.tools import get_financials
        with pytest.raises(ValueError, match="Invalid ts_code"):
            get_financials("bad", "income")

    def test_rejects_bad_statement(self):
        from tushare_db.mcp_server.tools import get_financials
        with pytest.raises(ValueError, match="Unknown statement"):
            get_financials("000001.SZ", "users")

    def test_rejects_bad_period(self):
        from tushare_db.mcp_server.tools import get_financials
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            with pytest.raises(ValueError, match="Invalid period"):
                get_financials("000001.SZ", "income", periods=["bad"])


class TestGetMoneyflowValidation:
    """get_moneyflow input validation."""

    def test_rejects_bad_ts_code(self):
        from tushare_db.mcp_server.tools import get_moneyflow
        with pytest.raises(ValueError, match="Invalid ts_code"):
            get_moneyflow("bad", "20240101", "20240131")

    def test_rejects_bad_dates(self):
        from tushare_db.mcp_server.tools import get_moneyflow
        with pytest.raises(ValueError, match="Invalid"):
            get_moneyflow("000001.SZ", "bad", "20240131")


class TestTradeCalendarValidation:
    """trade_calendar input validation."""

    def test_rejects_bad_dates(self):
        from tushare_db.mcp_server.tools import trade_calendar
        with pytest.raises(ValueError, match="Invalid"):
            trade_calendar("bad", "20240131")

    def test_rejects_bad_exchange(self):
        from tushare_db.mcp_server.tools import trade_calendar
        with pytest.raises(ValueError, match="Invalid exchange"):
            trade_calendar("20240101", "20240131", exchange="NYSE")


class TestCoverageReportValidation:
    """coverage_report input validation."""

    def test_rejects_bad_priority(self):
        from tushare_db.mcp_server.tools import coverage_report
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            with patch("tushare_db.config.loader.load_interface_specs", return_value=[]):
                with pytest.raises(ValueError, match="Invalid priority"):
                    coverage_report(priority="INVALID")


class TestGetIndexComponentsValidation:
    """get_index_components date validation."""

    def test_validates_date_param(self):
        from tushare_db.mcp_server.tools import get_index_components
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            with pytest.raises(ValueError, match="Invalid date"):
                get_index_components("000300.SH", date="bad")


class TestDescribeTableValidation:
    """describe_table database whitelist."""

    def test_rejects_system_database(self):
        from tushare_db.mcp_server.tools import describe_table
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            with pytest.raises(ValueError, match="Only tushare and _meta"):
                describe_table("system.users")

    def test_accepts_tushare_prefix(self):
        from tushare_db.mcp_server.tools import describe_table
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["name", "type", "default"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            result = describe_table("tushare.stock_basic")
            assert "columns" in result

    def test_accepts_meta_prefix(self):
        from tushare_db.mcp_server.tools import describe_table
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["name", "type", "default"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_get.return_value = mock_client

            result = describe_table("_meta.sync_state")
            assert "columns" in result

    def test_defaults_to_tushare(self):
        """Table without prefix should default to tushare."""
        from tushare_db.mcp_server.tools import describe_table
        with patch("tushare_db.mcp_server.tools._get_client") as mock_get:
            mock_client = MagicMock()

            def _mock_query(*args, **kwargs):
                result = MagicMock()
                if "DESCRIBE" in str(args[0]) if args else "":
                    result.column_names = ["name", "type", "default"]
                    result.result_rows = [("ts_code", "String", "")]
                elif "system.parts" in str(args[0]) if args else "":
                    result.result_rows = [(10000,)]
                elif "_version" in str(args[0]) if args else "":
                    result.result_rows = [(12345,)]
                else:
                    result.result_rows = []
                return result

            mock_client.query.side_effect = _mock_query
            mock_get.return_value = mock_client

            result = describe_table("stock_basic")
            assert result["table"] == "tushare.stock_basic"
