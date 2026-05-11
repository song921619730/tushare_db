"""Sync state writer: mark migrated tables as 'done' in _meta.sync_state."""

from __future__ import annotations

import time
from datetime import datetime, timezone


def write_sync_state_done(ch_client, spec) -> int:
    """Write 'done' records to _meta.sync_state for migrated table(s).

    For date-based tables, write one record per distinct trade_date.
    For non-date tables, write one 'full' record.

    Returns number of records written.
    """
    ch_table_full = f"{spec.ch_database}.{spec.ch_table}"

    if not spec.date_column:
        _insert_sync_state(
            ch_client,
            interface=spec.pg_table.replace("tushare_", ""),
            scope_key="full",
            rows=_get_total_rows(ch_client, ch_table_full),
        )
        return 1

    # Date-based: one record per distinct date
    result = ch_client.query(
        f"SELECT {spec.date_column}, count() FROM {ch_table_full} FINAL "
        f"GROUP BY {spec.date_column}"
    )
    count = 0
    for date_val, cnt in result.result_rows:
        scope_key = f"{spec.pg_table.replace('tushare_', '')}:{date_val.strftime('%Y%m%d')}"
        _insert_sync_state(
            ch_client,
            interface=spec.pg_table.replace("tushare_", ""),
            scope_key=scope_key,
            rows=int(cnt),
        )
        count += 1
    return count


def _insert_sync_state(ch_client, interface: str, scope_key: str, rows: int) -> None:
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    ch_client.insert(
        table="sync_state",
        data=[(interface, scope_key, "done", rows, now, now, 0, "", version)],
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts",
            "last_error", "_version",
        ],
        database="_meta",
    )


def write_sync_state_batch(ch_client, records: list[tuple]) -> None:
    """Batch insert sync_state records (faster than individual inserts)."""
    if not records:
        return
    ch_client.insert(
        table="sync_state",
        data=records,
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts",
            "last_error", "_version",
        ],
        database="_meta",
    )


def _get_total_rows(ch_client, ch_table_full: str) -> int:
    return int(ch_client.query(f"SELECT count() FROM {ch_table_full} FINAL").result_rows[0][0])
