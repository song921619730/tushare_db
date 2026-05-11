"""Sync state persistence: checkpoint tracking via _meta.sync_state.

Operations:
- upsert_running: mark unit as running with heartbeat
- upsert_done: mark unit as done with row count
- upsert_failed: mark unit as failed with error
- upsert_partial: mark stale running units as partial
- get_status: query sync state for an interface
- mark_stale_units: scan for units with stale heartbeat (>10 min)
"""

from __future__ import annotations

import uuid

import clickhouse_connect.driver
import structlog

from tushare_db.meta.sql_utils import escape_sql_str

logger = structlog.get_logger()


def mark_stale_units(
    client: clickhouse_connect.driver.Client,
    threshold_minutes: int = 10,
) -> int:
    """Mark stale running units as partial.

    Scans _meta.sync_state for units where status='running' AND
    heartbeat_at is older than threshold_minutes.

    Returns:
        Number of units marked as partial.
    """
    result = client.command(
        f"SELECT count() FROM _meta.sync_state FINAL "
        f"WHERE status = 'running' "
        f"AND heartbeat_at < now64(3, 'Asia/Shanghai') - INTERVAL {threshold_minutes} MINUTE"
    )
    stale_count = int(result) if result else 0

    if stale_count > 0:
        logger.info(
            "Marking stale units as partial",
            count=stale_count,
            threshold_minutes=threshold_minutes,
        )
        # Insert new rows with status='partial' for stale units
        client.command(
            "INSERT INTO _meta.sync_state "
            "(interface, scope_key, status, rows, last_success_at, heartbeat_at, attempts, last_error, _version) "
            f"SELECT interface, scope_key, 'partial', rows, last_success_at, heartbeat_at, attempts, "
            f"'heartbeat timeout', toUnixTimestamp64Milli(now64()) "
            "FROM _meta.sync_state FINAL "
            "WHERE status = 'running' "
            f"AND heartbeat_at < now64(3, 'Asia/Shanghai') - INTERVAL {threshold_minutes} MINUTE"
        )

    return stale_count


def get_interface_status(
    client: clickhouse_connect.driver.Client,
    interface: str,
) -> list[dict]:
    """Get sync status for all units of an interface."""
    result = client.query(
        "SELECT scope_key, status, rows, last_success_at, heartbeat_at, attempts, last_error "
        f"FROM _meta.sync_state FINAL WHERE interface = '{escape_sql_str(interface)}' ORDER BY scope_key"
    )
    rows = []
    for r in result.result_rows:
        rows.append({
            "scope_key": r[0],
            "status": r[1],
            "rows": r[2],
            "last_success_at": str(r[3]),
            "heartbeat_at": str(r[4]),
            "attempts": r[5],
            "last_error": r[6],
        })
    return rows


def get_pending_units(
    client: clickhouse_connect.driver.Client,
    interface: str,
) -> list[dict]:
    """Get units that are pending, failed, or partial (need retry)."""
    result = client.query(
        "SELECT scope_key, status, attempts "
        f"FROM _meta.sync_state FINAL WHERE interface = '{escape_sql_str(interface)}' "
        f"AND status IN ('pending', 'partial', 'failed') ORDER BY scope_key"
    )
    return [
        {"scope_key": r[0], "status": r[1], "attempts": r[2]}
        for r in result.result_rows
    ]
