"""Worker: execute a single work unit with heartbeat tracking.

Each worker:
1. Marks unit as 'running' in _meta.sync_state with initial heartbeat
2. Fetches data from Tushare API
3. Writes to ClickHouse
4. Updates _meta.sync_state to 'done'
5. Heartbeats every 30s during execution
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import clickhouse_connect.driver
import structlog

from tushare_db.planner.strategies import WorkUnit
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.errors import TushareBizError, TushareAuthError, TushareError
from tushare_db.sink.clickhouse_sink import insert_with_version
from tushare_db.schema.type_map import normalize_value

logger = structlog.get_logger()

HEARTBEAT_INTERVAL = 30  # seconds

_NOW = datetime(1970, 1, 1, tzinfo=timezone.utc)  # epoch sentinel for last_success_at

# Per-process cache of column types, keyed by "database.table"
_COLUMN_TYPE_CACHE: dict[str, dict[str, str]] = {}


def mark_running(
    client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    run_id: uuid.UUID,
    attempt: int = 0,
) -> None:
    """Mark a work unit as running in sync_state."""
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    client.insert(
        table="sync_state",
        data=[(
            unit.interface,
            unit.scope_key,
            "running",
            0,
            _NOW,
            now,
            attempt,
            "",
            version,
        )],
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
        ],
        database="_meta",
    )


def mark_done(
    client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    rows: int,
    attempt: int = 0,
) -> None:
    """Mark a work unit as done."""
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    client.insert(
        table="sync_state",
        data=[(
            unit.interface,
            unit.scope_key,
            "done",
            rows,
            now,
            now,
            attempt,
            "",
            version,
        )],
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
        ],
        database="_meta",
    )


def mark_failed(
    client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    error: str,
    attempt: int = 0,
) -> None:
    """Mark a work unit as failed."""
    version = int(time.time() * 1000)
    now = datetime.now(timezone.utc)
    client.insert(
        table="sync_state",
        data=[(
            unit.interface,
            unit.scope_key,
            "failed",
            0,
            _NOW,
            now,
            attempt,
            error[:500],
            version,
        )],
        column_names=[
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
        ],
        database="_meta",
    )


def execute_unit(
    unit: WorkUnit,
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID,
) -> int:
    """Execute a single work unit end-to-end.

    Returns:
        Number of rows written.
    """
    logger.info(
        "Executing work unit",
        interface=unit.interface,
        scope_key=unit.scope_key,
        run_id=str(run_id),
    )

    mark_running(ch_client, unit, run_id)

    attempt = unit.retries + 1
    stop_event = threading.Event()

    def _heartbeat_loop() -> None:
        """Background heartbeat that updates heartbeat_at every HEARTBEAT_INTERVAL.

        Sends first heartbeat immediately so stale detection starts from now.
        """
        try:
            version = int(time.time() * 1000)
            ch_client.insert(
                table="sync_state",
                data=[(
                    unit.interface,
                    unit.scope_key,
                    "running",
                    0,
                    _NOW,
                    datetime.now(timezone.utc),
                    attempt,
                    "",
                    version,
                )],
                column_names=[
                    "interface", "scope_key", "status", "rows",
                    "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
                ],
                database="_meta",
            )
        except Exception:
            logger.warning("Heartbeat failed", interface=unit.interface, scope_key=unit.scope_key)

        while not stop_event.is_set():
            stop_event.wait(HEARTBEAT_INTERVAL)
            if not stop_event.is_set():
                try:
                    version = int(time.time() * 1000)
                    ch_client.insert(
                        table="sync_state",
                        data=[(
                            unit.interface,
                            unit.scope_key,
                            "running",
                            0,
                            _NOW,
                            datetime.now(timezone.utc),
                            attempt,
                            "",
                            version,
                        )],
                        column_names=[
                            "interface", "scope_key", "status", "rows",
                            "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
                        ],
                        database="_meta",
                    )
                except Exception:
                    logger.warning("Heartbeat failed", interface=unit.interface, scope_key=unit.scope_key)

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    try:
        # Fetch data from Tushare
        api_response = tushare_client.call(
            unit.interface,
            bucket=unit.bucket,
            **unit.params,
        )

        # Parse response
        fields = api_response.get("data", {}).get("fields", [])
        items = api_response.get("data", {}).get("items", [])

        if not items:
            logger.warning("Empty response", interface=unit.interface, scope_key=unit.scope_key)
            mark_done(ch_client, unit, 0, attempt)
            return 0

        # Normalize: dates + 万元→元 + 万份→份
        column_types = _get_column_types(ch_client, unit.table)
        normalized_items = _normalize_items(fields, items, column_types=column_types)

        # Write to ClickHouse
        insert_with_version(
            ch_client,
            table=unit.table,
            columns=fields,
            rows=normalized_items,
        )

        rows_written = len(normalized_items)
        mark_done(ch_client, unit, rows_written, attempt)

        logger.info(
            "Unit complete",
            interface=unit.interface,
            scope_key=unit.scope_key,
            rows=rows_written,
        )

        return rows_written

    except TushareBizError as e:
        mark_failed(ch_client, unit, str(e), attempt)
        logger.error("Business error", interface=unit.interface, scope_key=unit.scope_key, error=str(e))
        return -1  # Signal biz error
    except TushareAuthError as e:
        mark_failed(ch_client, unit, str(e), attempt)
        logger.error("Auth error", interface=unit.interface, scope_key=unit.scope_key, error=str(e))
        return -2
    except TushareError as e:
        mark_failed(ch_client, unit, str(e), attempt)
        logger.error("Tushare error", interface=unit.interface, scope_key=unit.scope_key, error=str(e))
        return -3
    except Exception as e:
        mark_failed(ch_client, unit, str(e), attempt)
        logger.error("Unexpected error", interface=unit.interface, scope_key=unit.scope_key, error=str(e))
        return -4
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=5)


def _get_column_types(
    ch_client: clickhouse_connect.driver.Client,
    table: str,
    database: str = "tushare",
) -> dict[str, str]:
    """Lazy-load column types for a table; cache per-process."""
    cache_key = f"{database}.{table}"
    if cache_key in _COLUMN_TYPE_CACHE:
        return _COLUMN_TYPE_CACHE[cache_key]

    result = ch_client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE database = '{database}' AND table = '{table}'"
    )
    type_map = {row[0]: row[1] for row in result.result_rows}
    _COLUMN_TYPE_CACHE[cache_key] = type_map
    return type_map


def _normalize_items(
    fields: list[str],
    items: list[list],
    column_types: dict[str, str] | None = None,
) -> list[list]:
    """Normalize values: dates + 万元→元 + 万份→份."""
    normalized = []
    date_indices = [i for i, f in enumerate(fields) if "date" in f.lower() or "ann_date" in f.lower()]
    column_types = column_types or {}

    for item in items:
        row = list(item)

        # 1. Date normalization
        for idx in date_indices:
            if idx < len(row) and row[idx] and isinstance(row[idx], str):
                val = row[idx].strip()
                if len(val) == 8 and val.isdigit():
                    row[idx] = datetime.strptime(val, "%Y%m%d").date()

        # 2. 万元/万份 normalization for Decimal64 columns
        for idx, field_name in enumerate(fields):
            if idx >= len(row) or row[idx] is None:
                continue
            ch_type = column_types.get(field_name, "")
            base_type = ch_type
            if base_type.startswith("Nullable("):
                base_type = base_type[len("Nullable("):-1]
            if base_type.startswith("Decimal64"):
                row[idx] = normalize_value(field_name, base_type, row[idx])

        normalized.append(row)

    return normalized
