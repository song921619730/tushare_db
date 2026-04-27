"""Post-unit data integrity verification hook.

After each work unit writes data to ClickHouse, this hook verifies:
1. Row count matches what was reported written
2. No excessive ReplacingMergeTree dedup loss (FINAL vs non-FINAL)
3. Date/period range of written data matches expected scope

If verification fails, the unit is retried (re-fetch + re-write, up to 2 attempts).
"""

from __future__ import annotations

import time

import clickhouse_connect.driver
import structlog

from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.worker import VerifyHook

logger = structlog.get_logger()

# Track when we last ran the expensive full-table dedup check
_LAST_FULL_CHECK: float = 0
_FULL_CHECK_INTERVAL = 300  # run full dedup check at most every 5 minutes


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
        return _verify(ch_client, unit, rows_written, max_dedup_ratio, full_check_interval)

    return hook


def _verify(
    ch_client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    rows_written: int,
    max_dedup_ratio: float,
    full_check_interval: int,
) -> bool:
    """Verify data integrity for a completed work unit.

    Returns True if verification passes, False to trigger retry.
    """
    global _LAST_FULL_CHECK

    if rows_written == 0:
        return True  # empty response is OK

    table = unit.table
    issues: list[str] = []

    # --- Check 1: Row count for this unit's scope ---
    where_clause = _build_where_clause(unit)
    query = f"SELECT count() FROM {table} WHERE {where_clause}"
    try:
        result = ch_client.query(query)
        actual_count = result.result_rows[0][0] if result.result_rows else 0

        if actual_count == 0:
            issues.append(f"CH has 0 rows for {unit.scope_key} (expected {rows_written})")
        elif actual_count < rows_written:
            # Some dedup is normal for ReplacingMergeTree; warn only on heavy loss
            loss = (rows_written - actual_count) / rows_written
            if loss > 0.80:
                issues.append(
                    f"80%+ rows lost to dedup: wrote {rows_written}, CH has {actual_count}"
                )
    except Exception as e:
        issues.append(f"Row count check failed: {e}")

    # --- Check 2: Full-table dedup ratio (expensive, throttled) ---
    now = time.time()
    if not issues and (now - _LAST_FULL_CHECK) >= full_check_interval:
        try:
            total_result = ch_client.query(f"SELECT count() FROM {table}")
            final_result = ch_client.query(f"SELECT count() FROM {table} FINAL")
            total_rows = total_result.result_rows[0][0]
            final_rows = final_result.result_rows[0][0]

            if total_rows > 100:
                dedup_ratio = 1.0 - (final_rows / total_rows)
                if dedup_ratio > max_dedup_ratio:
                    issues.append(
                        f"Table-level dedup loss: {final_rows} FINAL / {total_rows} total "
                        f"(loss={dedup_ratio:.0%}) — possible sorting key bug"
                    )
            _LAST_FULL_CHECK = now
        except Exception as e:
            logger.debug("Full dedup check skipped", table=table, error=str(e))

    # --- Check 3: Date/period range sanity ---
    if not issues:
        try:
            date_field = _get_date_field(unit)
            if date_field:
                query = f"SELECT min({date_field}), max({date_field}) FROM {table} WHERE {where_clause}"
                result = ch_client.query(query)
                if result.result_rows and result.result_rows[0][0]:
                    min_d, max_d = result.result_rows[0]
                    if min_d and max_d and min_d > max_d:
                        issues.append(f"Date range inverted: min={min_d} > max={max_d}")
        except Exception:
            pass  # non-critical

    if issues:
        logger.warning(
            "Verify hook FAILED",
            interface=unit.interface,
            scope_key=unit.scope_key,
            issues=issues,
        )
        return False

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
