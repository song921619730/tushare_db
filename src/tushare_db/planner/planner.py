"""Planner: generate work units from interface specs and trade calendar."""

from __future__ import annotations

import uuid

import clickhouse_connect.driver
import structlog

from tushare_db.config.models import InterfaceSpec
from tushare_db.planner.strategies import (
    WorkUnit,
    generate_full_once_units,
    generate_date_loop_units,
    generate_period_loop_units,
    generate_monthly_window_units,
    generate_per_symbol_period_units,
    generate_offset_paging_units,
)

logger = structlog.get_logger()


def _validate_date(date_str: str) -> str:
    """Validate YYYYMMDD date format. Raises ValueError on invalid input."""
    if not isinstance(date_str, str) or len(date_str) != 8 or not date_str.isdigit():
        raise ValueError(f"Invalid date format: {date_str!r}, expected YYYYMMDD")
    # Verify it's a real date
    from datetime import datetime
    datetime.strptime(date_str, "%Y%m%d")
    return date_str


def get_trade_dates(
    client: clickhouse_connect.driver.Client,
    start_date: str,
    end_date: str,
) -> list[str]:
    """Query trading calendar from tushare.trade_cal table."""
    _validate_date(start_date)
    _validate_date(end_date)
    result = client.query(
        f"SELECT cal_date FROM _meta.trade_cal "
        f"WHERE cal_date >= '{start_date}' AND cal_date <= '{end_date}' AND is_open = 1 "
        f"ORDER BY cal_date"
    )
    dates = []
    for row in result.result_rows:
        dt = row[0]
        # Convert to YYYYMMDD string
        if hasattr(dt, "strftime"):
            dates.append(dt.strftime("%Y%m%d"))
        else:
            dates.append(str(dt).replace("-", "")[:8])
    return dates


def get_symbols(
    client: clickhouse_connect.driver.Client,
) -> list[str]:
    """Get all active stock symbols from stock_basic."""
    # Check if stock_basic exists before querying
    result = client.query(
        "SELECT count() FROM system.tables "
        "WHERE database = 'tushare' AND name = 'tushare_stock_basic'"
    )
    if int(result.result_rows[0][0]) == 0:
        logger.warning("stock_basic table not found, returning empty symbol list")
        return []

    result = client.query(
        "SELECT ts_code FROM tushare.tushare_stock_basic ORDER BY ts_code"
    )
    return [row[0] for row in result.result_rows]


def plan_units(
    spec: InterfaceSpec,
    client: clickhouse_connect.driver.Client,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[WorkUnit]:
    """Generate all work units for a single interface.

    Args:
        spec: Interface specification from YAML.
        client: ClickHouse client (for trade_cal/symbols).
        start_date: Override start date. Uses spec.start_date if None.
        end_date: Override end date. Uses today if None.

    Returns:
        List of WorkUnit objects.
    """
    strategy = spec.fetch_strategy.kind
    bucket = spec.freq_bucket
    table = spec.table

    if strategy == "full_once":
        return generate_full_once_units(spec.name, bucket, table=table)

    if strategy in ("date_loop", "offset_paging"):
        dates = get_trade_dates(
            client,
            start_date or spec.start_date or "20200101",
            end_date or _today(),
        )
        if strategy == "offset_paging":
            return generate_offset_paging_units(spec.name, bucket, dates, table=table)
        return generate_date_loop_units(spec.name, bucket, dates, table=table)

    if strategy == "period_loop":
        return generate_period_loop_units(
            spec.name, bucket, table=table,
            start_date=start_date or spec.start_date or "20200101",
            end_date=end_date or _today(),
        )

    if strategy == "monthly_window":
        return generate_monthly_window_units(
            spec.name, bucket, table=table,
            start_date=start_date or spec.start_date or "20200101",
            end_date=end_date or _today(),
        )

    if strategy == "per_symbol_period":
        symbols = get_symbols(client)
        return generate_per_symbol_period_units(
            spec.name, bucket, table=table,
            symbols=symbols,
            start_date=start_date or spec.start_date or "20200101",
            end_date=end_date or _today(),
        )

    raise ValueError(f"Unknown strategy: {strategy}")


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")
