"""Incremental update: fetch T-1 data for enabled interfaces.

Unlike backfill which processes historical date ranges, incremental
update only fetches the most recent trading day (T-1) for each interface.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.config.models import InterfaceSpec
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import get_trade_dates, plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.runner.verify_hook import make_verify_hook

logger = structlog.get_logger()


def get_latest_trade_date(
    ch_client: clickhouse_connect.driver.Client,
) -> str | None:
    """Get the most recent trading date <= today from trade_cal."""
    today = datetime.now().strftime("%Y%m%d")
    result = ch_client.query(
        f"SELECT cal_date FROM _meta.trade_cal "
        f"WHERE is_open = 1 AND cal_date <= '{today}' "
        "ORDER BY cal_date DESC LIMIT 1"
    )
    if not result.result_rows:
        return None
    dt = result.result_rows[0][0]
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y%m%d")
    return str(dt).replace("-", "")[:8]


def get_target_date(
    ch_client: clickhouse_connect.driver.Client,
) -> str | None:
    """Get T-1 trading date (yesterday's trading day).

    Returns None if yesterday is not a trading day or trade_cal is empty.
    """
    latest = get_latest_trade_date(ch_client)
    if not latest:
        return None

    # Find the trading date before the latest one (T-1)
    result = ch_client.query(
        "SELECT cal_date FROM _meta.trade_cal "
        f"WHERE is_open = 1 AND cal_date < '{latest}' "
        "ORDER BY cal_date DESC LIMIT 1"
    )
    if not result.result_rows:
        return None
    dt = result.result_rows[0][0]
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y%m%d")
    return str(dt).replace("-", "")[:8]


def filter_by_batch(specs: list[InterfaceSpec], batch: str) -> list[InterfaceSpec]:
    """Filter interfaces by their batch assignment."""
    return [s for s in specs if s.batch == batch]


def run_incremental(
    ch_client: clickhouse_connect.driver.Client,
    tushare_client: TushareClient,
    batch: str | None = None,
) -> dict:
    """Run incremental T-1 update.

    Args:
        ch_client: ClickHouse client.
        tushare_client: Tushare API client.
        batch: Optional batch filter (A|B|C|D|saturday|reference).
               If None, runs all enabled interfaces.

    Returns:
        Summary dict with total/done/failed counts.
    """
    target_date = get_target_date(ch_client)
    if not target_date:
        logger.warning("No target trading date found for incremental update")
        return {"total": 0, "done": 0, "failed": 0, "reason": "no_target_date"}

    logger.info("Starting incremental update", target_date=target_date, batch=batch or "all")

    specs = load_interface_specs()
    specs = [s for s in specs if s.enabled]

    if batch:
        specs = filter_by_batch(specs, batch)

    if not specs:
        logger.warning("No matching interfaces for incremental update", batch=batch)
        return {"total": 0, "done": 0, "failed": 0, "reason": "no_matching_specs"}

    run_id = uuid.uuid4()
    total_units = 0
    total_done = 0
    total_failed = 0

    for spec in specs:
        # Plan units for the single target date
        units = plan_units(spec, ch_client, start_date=target_date, end_date=target_date)
        if not units:
            continue

        total_units += len(units)
        logger.info(
            "Planning incremental units",
            interface=spec.name,
            target_date=target_date,
            units=len(units),
        )

        _, done_count, failed_count = execute_batch(
            units, tushare_client, ch_client, run_id=run_id,
            verify_hook=make_verify_hook(),
        )
        total_done += done_count
        total_failed += failed_count

    result = {
        "total": total_units,
        "done": total_done,
        "failed": total_failed,
        "target_date": target_date,
        "batch": batch or "all",
    }

    logger.info("Incremental update complete", **result)
    return result
