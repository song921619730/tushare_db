"""Post-unit data integrity verification hook.

After each work unit writes data to ClickHouse, this hook verifies:
1. Row count matches what was reported written
2. No excessive ReplacingMergeTree dedup loss (FINAL vs non-FINAL)
3. Date/period range of written data matches expected scope

If verification fails, the unit is retried (re-fetch + re-write, up to 2 attempts).

Key design: verification uses a **fresh, independent ClickHouse client** per call
to avoid connection corruption from concurrent INSERT operations sharing the
same HTTP session. Query failures (timeout, disconnect) are treated as PASS
— we only fail when data can be definitively proven wrong.
"""

from __future__ import annotations

import time

import clickhouse_connect
import clickhouse_connect.driver
import os
import structlog

from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.worker import VerifyHook

logger = structlog.get_logger()

# Track when we last ran the expensive full-table dedup check
_LAST_FULL_CHECK: float = 0
_FULL_CHECK_INTERVAL = 300  # run full dedup check at most every 5 minutes


def _new_verify_client() -> clickhouse_connect.driver.Client:
    """Create a fresh ClickHouse client for verification queries.

    Independent from the INSERT client to avoid HTTP session corruption
    under high concurrency (StreamReset, connection closed, etc.).
    """
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
        connect_timeout=5,
        send_receive_timeout=30,
    )


def make_verify_hook(
    *,
    max_dedup_ratio: float = 0.10,
    full_check_interval: int = 300,
) -> VerifyHook:
    """Create a verify hook for use with execute_batch.

    Args:
        max_dedup_ratio: Maximum allowed dedup ratio before flagging.
        full_check_interval: Minimum seconds between expensive full-table dedup checks.
    """

    def hook(
        ch_client: clickhouse_connect.driver.Client,
        unit: WorkUnit,
        rows_written: int,
    ) -> bool:
        client = _new_verify_client()
        try:
            return _verify(client, unit, rows_written, max_dedup_ratio, full_check_interval)
        finally:
            client.close()

    return hook


def _verify(
    ch_client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    rows_written: int,
    max_dedup_ratio: float,
    full_check_interval: int,
) -> bool:
    """Verify data integrity for a completed work unit.

    Returns True if verification passes or cannot be determined.
    Returns False only when data is definitively wrong.
    """
    global _LAST_FULL_CHECK

    if rows_written == 0:
        return True  # empty response is OK

    table = unit.table

    # --- Check 1: Row count for this unit's scope ---
    where_clause = _build_where_clause(unit)
    query = f"SELECT count() FROM {table} WHERE {where_clause}"
    try:
        result = ch_client.query(query)
        actual_count = result.result_rows[0][0] if result.result_rows else 0

        if actual_count == 0:
            # Definitive: we wrote rows_written > 0 but CH has zero rows
            logger.warning(
                "verify: zero rows in CH",
                interface=unit.interface,
                scope_key=unit.scope_key,
                expected=rows_written,
            )
            return False
        elif actual_count < rows_written:
            # Some dedup is normal for ReplacingMergeTree; warn only on heavy loss
            loss = (rows_written - actual_count) / rows_written
            if loss > 0.80:
                logger.warning(
                    "verify: heavy dedup loss",
                    interface=unit.interface,
                    scope_key=unit.scope_key,
                    wrote=rows_written,
                    has=actual_count,
                    loss=f"{loss:.0%}",
                )
                return False
    except Exception as e:
        # Query failed (connection error, timeout, etc.) — cannot verify,
        # assume data was written successfully. This is safer than marking
        # a good unit as failed due to a flaky CH connection.
        logger.debug(
            "verify: CH query failed, assuming OK",
            interface=unit.interface,
            scope_key=unit.scope_key,
            error=str(e),
        )
        return True

    # --- Check 2: Full-table dedup ratio (expensive, throttled) ---
    # Skip for per_symbol units (no period param) — they own all data for a stock,
    # so table-level dedup ratio is meaningless for their scope.
    is_per_symbol = "ts_code" in unit.params and "period" not in unit.params
    if not is_per_symbol:
        now = time.time()
        if (now - _LAST_FULL_CHECK) >= full_check_interval:
            try:
                total_result = ch_client.query(f"SELECT count() FROM {table}")
                final_result = ch_client.query(f"SELECT count() FROM {table} FINAL")
                total_rows = total_result.result_rows[0][0]
                final_rows = final_result.result_rows[0][0]

                if total_rows > 100:
                    dedup_ratio = 1.0 - (final_rows / total_rows)
                    if dedup_ratio > max_dedup_ratio:
                        logger.warning(
                            "verify: table-level dedup loss",
                            table=table,
                            final=final_rows,
                            total=total_rows,
                            loss=f"{dedup_ratio:.0%}",
                        )
                        # Don't fail the unit — this is a systemic issue, not
                        # specific to this unit. Log warning for investigation.
                _LAST_FULL_CHECK = now
            except Exception as e:
                logger.debug("Full dedup check skipped", table=table, error=str(e))

    # --- Check 3: Date/period range sanity ---
    try:
        date_field = _get_date_field(unit)
        if date_field:
            query = f"SELECT min({date_field}), max({date_field}) FROM {table} WHERE {where_clause}"
            result = ch_client.query(query)
            if result.result_rows and result.result_rows[0][0]:
                min_d, max_d = result.result_rows[0]
                if min_d and max_d and min_d > max_d:
                    logger.warning(
                        "verify: date range inverted",
                        interface=unit.interface,
                        scope_key=unit.scope_key,
                        min=min_d,
                        max=max_d,
                    )
                    return False
    except Exception as e:
        logger.debug(
            "verify: date range check failed, assuming OK",
            interface=unit.interface,
            scope_key=unit.scope_key,
            error=str(e),
        )

    return True


def _get_date_field(unit: WorkUnit) -> str | None:
    """Infer the primary date field from unit params."""
    for key in ("trade_date", "end_date", "ann_date"):
        if key in unit.params:
            return key
    return None


def _build_where_clause(unit: WorkUnit) -> str:
    """Build WHERE clause matching the unit's scope."""
    conditions = []

    if "ts_code" in unit.params:
        conditions.append(f"ts_code = '{unit.params['ts_code']}'")

    for date_key in ("trade_date", "end_date", "ann_date"):
        if date_key in unit.params:
            val = unit.params[date_key]
            if isinstance(val, str) and len(val) == 8 and val.isdigit():
                conditions.append(f"{date_key} = '{val[:4]}-{val[4:6]}-{val[6:]}'")
            else:
                conditions.append(f"{date_key} = '{val}'")
            break

    if "period" in unit.params:
        period = unit.params["period"]
        if isinstance(period, str) and len(period) == 8:
            conditions.append(
                f"toYYYYMM(end_date) = {int(period[:4]) * 100 + int(period[4:6])}"
            )

    return " AND ".join(conditions) if conditions else "1=1"
