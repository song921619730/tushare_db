"""Sync runs audit: track each sync run's lifecycle in _meta.sync_runs."""

from __future__ import annotations

import uuid
from datetime import datetime

import clickhouse_connect.driver

from tushare_db.meta.sql_utils import escape_sql_str


def _now_shanghai() -> datetime:
    """Current time in Asia/Shanghai timezone as datetime object."""
    import zoneinfo
    return datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))


def create_run(
    client: clickhouse_connect.driver.Client,
    interface: str,
    batch: str,
    scope: str,
    units_total: int,
    run_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Create a new sync run entry.

    Returns:
        run_id UUID.
    """
    if run_id is None:
        run_id = uuid.uuid4()
    now = _now_shanghai()

    client.insert(
        table="sync_runs",
        data=[(
            str(run_id),
            interface,
            batch,
            scope,
            now,
            None,
            units_total,
            0,
            0,
            "running",
            0,
        )],
        column_names=[
            "run_id", "interface", "batch", "scope", "started_at", "finished_at",
            "units_total", "units_done", "units_failed", "status", "normalize_version",
        ],
        database="_meta",
    )

    return run_id


def update_run(
    client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID,
    units_done: int | None = None,
    units_failed: int | None = None,
    status: str | None = None,
) -> None:
    """Update a sync run's progress."""
    updates = []
    if units_done is not None:
        updates.append(f"units_done = {units_done}")
    if units_failed is not None:
        updates.append(f"units_failed = {units_failed}")
    if status is not None:
        updates.append(f"status = '{escape_sql_str(status)}'")
        if status in ("done", "partial", "failed"):
            now = _now_shanghai()
            updates.append(f"finished_at = '{escape_sql_str(now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])}'")

    if not updates:
        return

    set_clause = ", ".join(updates)
    client.command(
        f"ALTER TABLE _meta.sync_runs UPDATE {set_clause} WHERE run_id = '{run_id}'"
    )
