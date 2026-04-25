"""Scheduler job definitions: A/B/C/D batches + Saturday long-tail +
refresh_reference + weekly_reconcile + verify_row_counts.

All jobs check trade_cal before running to skip non-trading days.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.config.models import InterfaceSpec
from tushare_db.core.tushare_client import TushareClient
from tushare_db.meta.sql_utils import escape_sql_str
from tushare_db.runner.incremental import get_target_date, run_incremental

logger = structlog.get_logger()


def _is_trading_day(
    ch_client: clickhouse_connect.driver.Client,
    trade_date: str,
) -> bool:
    """Check if the given date is a trading day per _meta.trade_cal."""
    result = ch_client.query(
        f"SELECT count() FROM _meta.trade_cal "
        f"WHERE cal_date = '{escape_sql_str(trade_date)}' AND is_open = 1"
    )
    if not result.result_rows:
        return False
    count = int(result.result_rows[0][0])
    if count == 0:
        # Could be empty table OR a genuine non-trading day; check if table has any rows
        total = ch_client.query("SELECT count() FROM _meta.trade_cal")
        if total.result_rows and int(total.result_rows[0][0]) == 0:
            logger.error(
                "trade_cal is empty — run `tushare-db bootstrap` first. "
                "All batches will be skipped until trade_cal is populated.",
                today=trade_date,
            )
            raise RuntimeError("trade_cal not seeded; bootstrap required")
    return count > 0


def _today_str() -> str:
    """Today's date in YYYYMMDD format."""
    return datetime.now().strftime("%Y%m%d")


def run_batch(
    batch: str,
    ch_client: clickhouse_connect.driver.Client | None = None,
    tushare_client: TushareClient | None = None,
) -> dict:
    """Run a specific batch (A|B|C|D|saturday|reference).

    Checks trade_cal first. For Saturday batch, only runs per_symbol_period
    interfaces. For reference batch, runs full_once interfaces.
    """
    today = _today_str()

    # Need a client for trade_cal check
    need_cleanup = ch_client is None
    if ch_client is None:
        ch_client = _get_ch_client()
    if tushare_client is None:
        tushare_client = _get_tushare_client()

    try:
        is_trading = _is_trading_day(ch_client, today)

        # Reference and Saturday batches can run on non-trading days
        if batch not in ("reference", "saturday") and not is_trading:
            logger.info("Skipping batch — not a trading day", batch=batch, today=today)
            return {"skipped": True, "reason": "non_trading_day"}

        result = run_incremental(ch_client, tushare_client, batch=batch)
        logger.info("Batch complete", batch=batch, **result)
        return result
    finally:
        if need_cleanup:
            ch_client.close()


def run_saturday_longtail(
    ch_client: clickhouse_connect.driver.Client | None = None,
    tushare_client: TushareClient | None = None,
) -> dict:
    """Run Saturday long-tail: per_symbol_period interfaces only."""
    need_cleanup = ch_client is None
    if ch_client is None:
        ch_client = _get_ch_client()
    if tushare_client is None:
        tushare_client = _get_tushare_client()

    try:
        specs = load_interface_specs()
        per_symbol_specs = [
            s for s in specs
            if s.enabled and s.fetch_strategy.kind == "per_symbol_period"
        ]

        if not per_symbol_specs:
            logger.info("No per_symbol_period interfaces found")
            return {"skipped": True, "reason": "no_per_symbol_specs"}

        logger.info(
            "Saturday longtail starting",
            interfaces=[s.name for s in per_symbol_specs],
        )

        target_date = get_target_date(ch_client)
        if not target_date:
            return {"skipped": True, "reason": "no_target_date"}

        from tushare_db.planner.planner import plan_units
        from tushare_db.runner.executor import execute_batch

        run_id = uuid.uuid4()
        total_units = 0
        total_done = 0
        total_failed = 0

        for spec in per_symbol_specs:
            units = plan_units(spec, ch_client, start_date=target_date, end_date=target_date)
            if not units:
                continue

            total_units += len(units)
            _, done_count, failed_count = execute_batch(
                units, tushare_client, ch_client, run_id=run_id,
            )
            total_done += done_count
            total_failed += failed_count

        result = {
            "total": total_units,
            "done": total_done,
            "failed": total_failed,
            "batch": "saturday",
        }
        logger.info("Saturday longtail complete", **result)
        return result
    finally:
        if need_cleanup:
            ch_client.close()


def run_refresh_reference(
    ch_client: clickhouse_connect.driver.Client | None = None,
    tushare_client: TushareClient | None = None,
) -> dict:
    """Refresh reference tables: *_basic, *_company, *_classify, trade_cal."""
    return run_batch("reference", ch_client, tushare_client)


def run_weekly_reconcile(
    ch_client: clickhouse_connect.driver.Client | None = None,
) -> dict:
    """Weekly reconciliation: scan P0/P1 interfaces for gaps and report pending counts."""
    need_cleanup = ch_client is None
    if ch_client is None:
        ch_client = _get_ch_client()

    try:
        logger.info("Weekly reconciliation starting")

        from tushare_db.meta.sync_state import get_pending_units

        specs = load_interface_specs()
        p0_p1_specs = [
            s for s in specs
            if s.enabled and s.priority in ("P0", "P1")
        ]

        total_pending = 0
        for spec in p0_p1_specs:
            pending = get_pending_units(ch_client, spec.name)
            if pending:
                total_pending += len(pending)
                logger.info(
                    "Found pending units",
                    interface=spec.name,
                    pending=len(pending),
                )

        result = {"total_pending": total_pending, "interfaces_scanned": len(p0_p1_specs)}
        logger.info("Weekly reconciliation complete", **result)
        return result
    finally:
        if need_cleanup:
            ch_client.close()


def run_verify_row_counts(
    ch_client: clickhouse_connect.driver.Client | None = None,
) -> dict:
    """Verify row counts for T-1: warn if count=0 on a trading day."""
    need_cleanup = ch_client is None
    if ch_client is None:
        ch_client = _get_ch_client()

    try:
        target_date = get_target_date(ch_client)
        if not target_date:
            return {"skipped": True, "reason": "no_target_date"}

        is_trading = _is_trading_day(ch_client, target_date)
        if not is_trading:
            logger.info("Skipping verify — not a trading day", target_date=target_date)
            return {"skipped": True, "reason": "non_trading_day"}

        logger.info("Verifying row counts", target_date=target_date)

        specs = load_interface_specs()
        enabled_specs = [s for s in specs if s.enabled]

        zero_count_interfaces = []
        for spec in enabled_specs:
            # Check sync_state for rows synced on target_date
            result = ch_client.query(
                f"SELECT sum(rows) FROM _meta.sync_state FINAL "
                f"WHERE interface = '{escape_sql_str(spec.name)}' "
                f"AND status = 'done' "
                f"AND scope_key LIKE '%{escape_sql_str(target_date)}%'"
            )
            row = result.result_rows[0] if result.result_rows else (0,)
            total_rows = int(row[0]) if row[0] else 0

            if total_rows == 0:
                zero_count_interfaces.append(spec.name)
                logger.warning(
                    "Zero rows for interface on trading day",
                    interface=spec.name,
                    target_date=target_date,
                )

        result = {
            "target_date": target_date,
            "interfaces_checked": len(enabled_specs),
            "zero_count": len(zero_count_interfaces),
            "zero_interfaces": zero_count_interfaces,
        }
        logger.info("Verify row counts complete", **result)
        return result
    finally:
        if need_cleanup:
            ch_client.close()


def _get_ch_client() -> clickhouse_connect.driver.Client:
    """Create ClickHouse client from environment."""
    import os
    from tushare_db.sink.clickhouse_sink import get_native_client

    return get_native_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=8123,
        user="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
    )


def _get_tushare_client() -> TushareClient:
    """Create Tushare client from environment."""
    import os
    from tushare_db.core.tushare_client import TushareClient

    return TushareClient(
        token=os.environ.get("TUSHARE_TOKEN", ""),
    )
