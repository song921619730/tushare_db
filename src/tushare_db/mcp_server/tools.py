"""MCP Tools: query_sql, get_ohlcv, list_interfaces, describe_table,
get_financials, get_index_components, get_moneyflow, trade_calendar,
coverage_report.
"""

from __future__ import annotations

import os
import re
from typing import Any

import clickhouse_connect.driver
import structlog

from tushare_db.mcp_server.server import mcp
from tushare_db.mcp_server.encoding import encode_response

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Helpers: Input validation
# ---------------------------------------------------------------------------

_TS_CODE_RE = re.compile(r"^[0-9]{6}\.(SH|SZ|BJ)$")
_DATE_RE = re.compile(r"^[0-9]{8}$")
_EXCHANGE_RE = re.compile(r"^(SSE|SZSE|BSE|CFFEX|SHFE|DCE|CZCE)$")
_SELECT_RE = re.compile(r"^\s*(SELECT|WITH|SHOW|DESCRIBE)\s", re.IGNORECASE)


def _validate_ts_code(ts_code: str) -> str:
    if not _TS_CODE_RE.match(ts_code):
        raise ValueError(f"Invalid ts_code format (expected 000001.SZ): {ts_code!r}")
    return ts_code


def _validate_date(date: str, name: str = "date") -> str:
    if not _DATE_RE.match(date):
        raise ValueError(f"Invalid {name} format (expected YYYYMMDD): {date!r}")
    return date


def _validate_exchange(exchange: str) -> str:
    if not _EXCHANGE_RE.match(exchange):
        raise ValueError(f"Invalid exchange: {exchange!r}")
    return exchange


def _validate_statement(statement: str) -> str:
    valid = {"income", "balancesheet", "cashflow", "fina_indicator"}
    if statement not in valid:
        raise ValueError(f"Unknown statement type: {statement!r}. Choose from: {sorted(valid)}")
    return statement


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _get_client() -> clickhouse_connect.driver.Client:
    """Read-only ClickHouse client via ai_reader (readonly=2 enforced at DB layer)."""
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        user="ai_reader",
        password=os.environ.get("CH_AI_READER_PASSWORD", ""),
        database="tushare",
    )


def _rows_to_dicts(result) -> list[dict[str, Any]]:
    """Convert ClickHouse result to list of dicts."""
    columns = result.column_names or []
    rows = []
    for row in result.result_rows:
        d = {}
        for i, col in enumerate(columns):
            val = row[i] if i < len(row) else None
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col] = val
        rows.append(d)
    return rows


def _safe_query(client: clickhouse_connect.driver.Client, sql: str) -> list[dict[str, Any]]:
    """Execute a SELECT-only query with validation."""
    if not _SELECT_RE.match(sql):
        raise ValueError(
            "Only SELECT, WITH, SHOW, DESCRIBE statements are allowed. "
            f"Query must start with one of these, got: {sql[:50]!r}"
        )
    result = client.query(sql)
    return _rows_to_dicts(result)


def _param_query(client: clickhouse_connect.driver.Client, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute a parameterized query (prevents SQL injection)."""
    if not _SELECT_RE.match(sql):
        raise ValueError(
            "Only SELECT, WITH, SHOW, DESCRIBE statements are allowed."
        )
    result = client.query(sql, parameters=params)
    return _rows_to_dicts(result)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def query_sql(sql: str) -> dict[str, Any]:
    """Execute a read-only SQL query against the Tushare database.

    Only SELECT, WITH, SHOW, and DESCRIBE statements are allowed.
    Results >1000 rows are returned as Arrow IPC + LZ4 (base64).
    """
    client = _get_client()
    try:
        rows = _safe_query(client, sql)
    finally:
        client.close()
    return encode_response(rows)


@mcp.tool()
def get_ohlcv(
    ts_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
) -> dict[str, Any]:
    """Get OHLCV (Open/High/Low/Close/Volume) data for a stock.

    Args:
        ts_code: Tushare stock code (e.g. "000001.SZ").
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.
        adjust: Adjustment type — "qfq" (forward), "hfq" (backward), or "none".

    Returns:
        List of OHLCV records with trade_date, open, high, low, close, vol, amount.
    """
    _validate_ts_code(ts_code)
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    valid_adjust = {"qfq", "hfq", "none"}
    if adjust not in valid_adjust:
        raise ValueError(f"adjust must be one of {sorted(valid_adjust)}, got {adjust!r}")

    client = _get_client()
    try:
        params = {"ts_code": ts_code, "start_date": start_date, "end_date": end_date}

        if adjust == "none":
            sql = (
                "SELECT trade_date, open, high, low, close, vol, amount, pct_chg "
                "FROM tushare.tushare_stock_daily FINAL "
                "WHERE ts_code = %(ts_code)s "
                "AND trade_date >= %(start_date)s AND trade_date <= %(end_date)s "
                "ORDER BY trade_date"
            )
        elif adjust == "qfq":
            sql = (
                "WITH latest AS ("
                "  SELECT adj_factor FROM tushare.tushare_adj_factor FINAL "
                "  WHERE ts_code = %(ts_code)s ORDER BY trade_date DESC LIMIT 1"
                ") "
                "SELECT d.trade_date, "
                "round(d.open  * af.adj_factor / latest.adj_factor, 4) AS open, "
                "round(d.high  * af.adj_factor / latest.adj_factor, 4) AS high, "
                "round(d.low   * af.adj_factor / latest.adj_factor, 4) AS low, "
                "round(d.close * af.adj_factor / latest.adj_factor, 4) AS close, "
                "d.vol, d.amount, d.pct_chg "
                "FROM tushare.tushare_stock_daily AS d FINAL "
                "INNER JOIN tushare.tushare_adj_factor AS af FINAL "
                "  ON d.ts_code = af.ts_code AND d.trade_date = af.trade_date "
                "CROSS JOIN latest "
                "WHERE d.ts_code = %(ts_code)s "
                "AND d.trade_date >= %(start_date)s AND d.trade_date <= %(end_date)s "
                "ORDER BY d.trade_date"
            )
        elif adjust == "hfq":
            sql = (
                "SELECT d.trade_date, "
                "round(d.open  * af.adj_factor, 4) AS open, "
                "round(d.high  * af.adj_factor, 4) AS high, "
                "round(d.low   * af.adj_factor, 4) AS low, "
                "round(d.close * af.adj_factor, 4) AS close, "
                "d.vol, d.amount, d.pct_chg "
                "FROM tushare.tushare_stock_daily AS d FINAL "
                "INNER JOIN tushare.tushare_adj_factor AS af FINAL "
                "  ON d.ts_code = af.ts_code AND d.trade_date = af.trade_date "
                "WHERE d.ts_code = %(ts_code)s "
                "AND d.trade_date >= %(start_date)s AND d.trade_date <= %(end_date)s "
                "ORDER BY d.trade_date"
            )
        else:
            raise AssertionError("unreachable")

        return encode_response(_param_query(client, sql, params))
    finally:
        client.close()


@mcp.tool()
def list_interfaces(category: str | None = None) -> dict[str, Any]:
    """List all available data interfaces with their sync status.

    Args:
        category: Optional filter by priority (P0/P1/P2/P3) or batch (A/B/C/D).

    Returns:
        Encoded response with list of interface specs.
    """
    from tushare_db.config.loader import load_interface_specs

    specs = load_interface_specs()
    result = []
    for s in specs:
        if not s.enabled:
            continue
        if category:
            if category.upper() in ("P0", "P1", "P2", "P3"):
                if s.priority != category.upper():
                    continue
            elif category.upper() in ("A", "B", "C", "D", "SATURDAY", "REFERENCE"):
                if s.batch.lower() != category.lower():
                    continue

        result.append({
            "name": s.name,
            "table": s.table,
            "priority": s.priority,
            "batch": s.batch,
            "strategy": s.fetch_strategy.kind,
            "mode": s.mode,
        })
    return encode_response(result)


@mcp.tool()
def describe_table(table: str) -> dict[str, Any]:
    """Get schema and stats for a specific table.

    Args:
        table: Table name (with or without tushare. prefix).

    Returns:
        Dict with columns, row count, and last update time.
    """
    client = _get_client()
    try:
        # Normalize table name — only allow tushare.* or _meta.*
        if "." in table:
            parts = table.split(".", 1)
            db_name, tbl_name = parts
            if db_name not in ("tushare", "_meta"):
                raise ValueError(f"Only tushare and _meta databases allowed, got {db_name!r}")
            full_name = table
        else:
            db_name, tbl_name = "tushare", table
            full_name = f"tushare.{table}"

        # Get columns
        col_result = client.query(f"DESCRIBE {full_name}")
        columns = []
        for row in col_result.result_rows:
            columns.append({
                "name": row[0],
                "type": row[1],
                "default": row[2],
            })

        # Get approximate row count from system.parts (fast, no FULL scan)
        count_result = client.query(
            "SELECT sum(rows) FROM system.parts "
            "WHERE database = %(db)s AND table = %(tbl)s AND active = 1",
            parameters={"db": db_name, "tbl": tbl_name},
        )
        row_count = int(count_result.result_rows[0][0] or 0) if count_result.result_rows else 0

        # Get last update version
        last_result = client.query(
            f"SELECT max(_version) FROM {full_name}"
        )
        last_update = None
        if last_result.result_rows and last_result.result_rows[0][0]:
            last_update = str(last_result.result_rows[0][0])

        return {
            "table": full_name,
            "columns": columns,
            "row_count": row_count,
            "column_count": len(columns),
            "last_update_version": last_update,
        }
    finally:
        client.close()


@mcp.tool()
def get_financials(
    ts_code: str,
    statement: str = "income",
    periods: list[str] | None = None,
) -> dict[str, Any]:
    """Get financial statement data for a stock.

    Args:
        ts_code: Tushare stock code (e.g. "000001.SZ").
        statement: Statement type — "income", "balancesheet", "cashflow", "fina_indicator".
        periods: Optional list of periods (e.g. ["20231231", "20230930"]).
                 If None, returns all available data.

    Returns:
        Encoded response with financial records.
    """
    _validate_ts_code(ts_code)
    _validate_statement(statement)

    client = _get_client()
    try:
        table_map = {
            "income": "tushare.tushare_income",
            "balancesheet": "tushare.tushare_balancesheet",
            "cashflow": "tushare.tushare_cashflow",
            "fina_indicator": "tushare.tushare_fina_indicator",
        }
        table = table_map[statement]

        sql = f"SELECT * FROM {table} FINAL WHERE ts_code = %(ts_code)s"
        params: dict[str, Any] = {"ts_code": ts_code}

        if periods:
            for p in periods:
                _validate_date(p, "period")
            sql += " AND end_date IN %(periods)s"
            params["periods"] = tuple(periods)

        sql += " ORDER BY end_date DESC"

        return encode_response(_param_query(client, sql, params))
    finally:
        client.close()


@mcp.tool()
def get_index_components(
    index_code: str,
    date: str | None = None,
) -> dict[str, Any]:
    """Get constituent stocks of an index.

    Args:
        index_code: Index code (e.g. "000300.SH" for CSI 300).
        date: Optional date in YYYYMMDD format for historical composition.

    Returns:
        Encoded response with constituent stock codes and weights.
    """
    client = _get_client()
    try:
        sql = "SELECT * FROM tushare.tushare_index_weight WHERE index_code = %(index_code)s"
        params: dict[str, Any] = {"index_code": index_code}

        if date:
            _validate_date(date, "date")
            sql += " AND trade_date = %(date)s"
            params["date"] = date

        sql += " ORDER BY con_code"

        return encode_response(_param_query(client, sql, params))
    finally:
        client.close()


@mcp.tool()
def get_moneyflow(
    ts_code: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Get money flow (capital inflow/outflow) data for a stock.

    Args:
        ts_code: Tushare stock code (e.g. "000001.SZ").
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.

    Returns:
        Encoded response with money flow records.
    """
    _validate_ts_code(ts_code)
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    client = _get_client()
    try:
        sql = (
            "SELECT * FROM tushare.tushare_moneyflow "
            "WHERE ts_code = %(ts_code)s "
            "AND trade_date >= %(start_date)s AND trade_date <= %(end_date)s "
            "ORDER BY trade_date"
        )
        params = {"ts_code": ts_code, "start_date": start_date, "end_date": end_date}
        return encode_response(_param_query(client, sql, params))
    finally:
        client.close()


@mcp.tool()
def trade_calendar(
    start_date: str,
    end_date: str,
    exchange: str = "SSE",
) -> dict[str, Any]:
    """Get trading calendar for a date range.

    Args:
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.
        exchange: Exchange code (default: "SSE").

    Returns:
        Encoded response with trading days and is_open flag.
    """
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")
    _validate_exchange(exchange)

    client = _get_client()
    try:
        sql = (
            "SELECT cal_date, is_open, pretrade_date "
            "FROM _meta.trade_cal "
            "WHERE exchange = %(exchange)s "
            "AND cal_date >= %(start_date)s AND cal_date <= %(end_date)s "
            "ORDER BY cal_date"
        )
        params = {"exchange": exchange, "start_date": start_date, "end_date": end_date}
        return encode_response(_param_query(client, sql, params))
    finally:
        client.close()


@mcp.tool()
def coverage_report(
    interface: str | None = None,
    priority: str | None = None,
) -> dict[str, Any]:
    """Get sync status and coverage report for interfaces.

    Args:
        interface: Optional specific interface name.
        priority: Optional filter by priority (P0/P1/P2/P3).

    Returns:
        Encoded response with coverage reports per interface.
    """
    from tushare_db.config.loader import load_interface_specs

    client = _get_client()
    try:
        specs = load_interface_specs()
        enabled_specs = [s for s in specs if s.enabled]

        if priority:
            valid_priority = {"P0", "P1", "P2", "P3"}
            if priority.upper() not in valid_priority:
                raise ValueError(f"Invalid priority: {priority!r}. Choose from: {sorted(valid_priority)}")
            enabled_specs = [s for s in enabled_specs if s.priority == priority.upper()]
        if interface:
            enabled_specs = [s for s in enabled_specs if s.name == interface]

        results = []
        for spec in enabled_specs:
            # Parameterized query for sync state
            status_result = client.query(
                "SELECT status, count(), sum(rows) "
                "FROM _meta.sync_state FINAL "
                "WHERE interface = %(iface)s "
                "GROUP BY status",
                parameters={"iface": spec.name},
            )

            status_map = {}
            total_rows = 0
            for row in status_result.result_rows:
                status_map[row[0]] = row[1]
                total_rows += int(row[2] or 0)

            last_sync_result = client.query(
                "SELECT max(heartbeat_at) FROM _meta.sync_state FINAL "
                "WHERE interface = %(iface)s AND status = 'done'",
                parameters={"iface": spec.name},
            )
            last_sync = None
            if last_sync_result.result_rows and last_sync_result.result_rows[0][0]:
                val = last_sync_result.result_rows[0][0]
                if hasattr(val, "isoformat"):
                    last_sync = val.isoformat()
                else:
                    last_sync = str(val)

            done_count = status_map.get("done", 0)
            partial_count = status_map.get("partial", 0)
            failed_count = status_map.get("failed", 0)

            if done_count > 0 and partial_count == 0 and failed_count == 0:
                status = "healthy"
            elif failed_count > 0:
                status = "failed"
            elif partial_count > 0:
                status = "partial"
            elif done_count == 0:
                status = "not_started"
            else:
                status = "in_progress"

            results.append({
                "interface": spec.name,
                "status": status,
                "last_sync": last_sync,
                "rows": total_rows,
                "sync_state_done": done_count,
                "sync_state_partial": partial_count,
                "sync_state_failed": failed_count,
            })

        return encode_response(results)
    finally:
        client.close()
