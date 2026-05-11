"""API call audit logging: mirror _meta.api_calls from application side."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

import clickhouse_connect.driver


def log_api_call(
    client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID,
    interface: str,
    params_hash: int,
    duration_ms: int,
    status: int,
    rows: int,
    error_msg: str = "",
) -> None:
    """Log a single API call to _meta.api_calls."""
    client.insert(
        table="api_calls",
        data=[(
            str(run_id),
            interface,
            params_hash,
            datetime.now(timezone.utc),
            duration_ms,
            status,
            rows,
            error_msg[:500],
        )],
        column_names=[
            "run_id", "interface", "params_hash", "started_at",
            "duration_ms", "status", "rows", "error_msg",
        ],
        database="_meta",
    )
