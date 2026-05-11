"""Row count verification: compare expected vs actual row counts per interface."""

from __future__ import annotations

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.runner.incremental import get_latest_trade_date

logger = structlog.get_logger()


def verify_row_counts(
    ch_client: clickhouse_connect.driver.Client,
    priority: str | None = None,
    interface: str | None = None,
) -> list[dict]:
    """Verify row counts for enabled interfaces.

    Args:
        ch_client: ClickHouse client.
        priority: Optional filter by priority (P0/P1/P2/P3).
        interface: Optional specific interface name.

    Returns:
        List of verification results per interface.
    """
    specs = load_interface_specs()
    enabled = [s for s in specs if s.enabled]

    if priority:
        enabled = [s for s in enabled if s.priority == priority.upper()]
    if interface:
        enabled = [s for s in enabled if s.name == interface]

    results = []
    for spec in enabled:
        table_name = spec.table
        if "." not in table_name:
            table_name = f"tushare.{table_name}"

        # Check if table exists
        table_check = ch_client.query(
            f"SELECT count() FROM system.tables "
            f"WHERE database = 'tushare' AND name = '{table_name.split('.')[-1]}'"
        )
        if int(table_check.result_rows[0][0]) == 0:
            results.append({
                "interface": spec.name,
                "table": table_name,
                "status": "missing",
                "row_count": 0,
                "issue": "Table does not exist",
            })
            continue

        # Get actual row count
        count_result = ch_client.query(f"SELECT count() FROM {table_name} FINAL")
        row_count = int(count_result.result_rows[0][0]) if count_result.result_rows else 0

        # Get sync state summary
        status_result = ch_client.query(
            f"SELECT status, count() FROM _meta.sync_state FINAL "
            f"WHERE interface = '{spec.name}' GROUP BY status"
        )
        status_map = {r[0]: r[1] for r in status_result.result_rows}

        done_count = status_map.get("done", 0)
        partial_count = status_map.get("partial", 0)
        failed_count = status_map.get("failed", 0)

        if row_count == 0 and done_count == 0:
            status = "empty"
        elif failed_count > 0:
            status = "has_failures"
        elif partial_count > 0:
            status = "has_partial"
        else:
            status = "ok"

        results.append({
            "interface": spec.name,
            "table": table_name,
            "status": status,
            "row_count": row_count,
            "sync_done": done_count,
            "sync_partial": partial_count,
            "sync_failed": failed_count,
        })

    return results
