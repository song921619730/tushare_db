"""Migration state tracking: _meta.migration_state CRUD."""

from __future__ import annotations

import time
from datetime import datetime, timezone


def ensure_state_table(ch_client) -> None:
    """Create _meta.migration_state if not exists."""
    ch_client.command("""
        CREATE TABLE IF NOT EXISTS _meta.migration_state (
            pg_table String,
            ch_table String,
            ch_database String,
            status Enum8('pending'=0,'running'=1,'done'=2,'failed'=3),
            rows_migrated UInt64,
            pg_row_count UInt64,
            started_at DateTime64(3, 'Asia/Shanghai'),
            finished_at Nullable(DateTime64(3, 'Asia/Shanghai')),
            duration_sec UInt32,
            error_msg String,
            _version UInt64
        ) ENGINE = ReplacingMergeTree(_version) ORDER BY pg_table
    """)


def get_status(ch_client, pg_table: str) -> str | None:
    """Return current status, or None if no record."""
    result = ch_client.query(
        f"SELECT status FROM _meta.migration_state FINAL WHERE pg_table='{pg_table}'"
    )
    if not result.result_rows:
        return None
    return str(result.result_rows[0][0])


def mark_running(ch_client, spec, pg_row_count: int) -> None:
    _insert(ch_client, spec, "running", 0, pg_row_count, None, "")


def mark_done(ch_client, spec, rows_migrated: int) -> None:
    _insert(ch_client, spec, "done", rows_migrated, 0, None, "")


def mark_failed(ch_client, spec, error: str) -> None:
    _insert(ch_client, spec, "failed", 0, 0, None, error[:500])


def _insert(
    ch_client, spec, status: str, rows: int, pg_count: int | None,
    duration: int | None, error: str,
) -> None:
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    finished = now if status == "done" else None
    ch_client.insert(
        table="migration_state",
        data=[(
            spec.pg_table, spec.ch_table, spec.ch_database,
            status, rows, pg_count, now, finished,
            duration or 0, error, version,
        )],
        column_names=[
            "pg_table", "ch_table", "ch_database", "status", "rows_migrated",
            "pg_row_count", "started_at", "finished_at", "duration_sec",
            "error_msg", "_version",
        ],
        database="_meta",
    )
