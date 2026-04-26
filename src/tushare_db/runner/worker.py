"""Worker: execute a single work unit with heartbeat tracking.

Each worker:
1. Marks unit as 'running' in _meta.sync_state with initial heartbeat
2. Fetches data from Tushare API
3. Writes to ClickHouse
4. Updates _meta.sync_state to 'done'
5. Heartbeats every 30s during execution
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timezone

import clickhouse_connect
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
_EPOCH_DATE = datetime(1970, 1, 1).date()  # default for non-nullable Date columns with None

# Per-process cache of column types with TTL, keyed by "database.table"
_COLUMN_TYPE_CACHE: dict[str, tuple[dict[str, str], float]] = {}
_CACHE_TTL = 300  # 5 minutes
_CACHE_LOCK = threading.Lock()


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


def _heartbeat_once(
    client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    attempt: int,
) -> None:
    """Send a single heartbeat row to _meta.sync_state."""
    version = int(time.time() * 1000)
    client.insert(
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


def _heartbeat_loop(
    client: clickhouse_connect.driver.Client,
    unit: WorkUnit,
    attempt: int,
    stop_event: threading.Event,
) -> None:
    """Background heartbeat using an independent ClickHouse client.

    Sends first heartbeat immediately, then repeats every HEARTBEAT_INTERVAL.
    """
    try:
        _heartbeat_once(client, unit, attempt)
    except Exception:
        logger.warning("Heartbeat failed", interface=unit.interface, scope_key=unit.scope_key)

    while not stop_event.is_set():
        stop_event.wait(HEARTBEAT_INTERVAL)
        if not stop_event.is_set():
            try:
                _heartbeat_once(client, unit, attempt)
            except Exception:
                logger.warning("Heartbeat failed", interface=unit.interface, scope_key=unit.scope_key)


def _new_ch_client(database: str = "tushare") -> clickhouse_connect.driver.Client:
    """Create a new ClickHouse client from environment configuration."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database=database,
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

    # N4: Heartbeat uses independent ClickHouse client to avoid
    # HTTP socket corruption when concurrent with main INSERT.
    heartbeat_client = _new_ch_client(database="_meta")

    try:
        _heartbeat_once(heartbeat_client, unit, attempt)

        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(heartbeat_client, unit, attempt, stop_event),
            daemon=True,
        )
        heartbeat_thread.start()

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
        return -1
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
        heartbeat_client.close()


def invalidate_column_cache(database: str | None = None, table: str | None = None) -> None:
    """Invalidate cached column types after schema evolution.

    Args:
        database: If set and table is None, invalidate all tables in that database.
        table: If set with database, invalidate only that specific table.
        Neither set: clear entire cache.
    """
    with _CACHE_LOCK:
        if database is None:
            _COLUMN_TYPE_CACHE.clear()
        elif table is None:
            prefix = f"{database}."
            for key in list(_COLUMN_TYPE_CACHE):
                if key.startswith(prefix):
                    del _COLUMN_TYPE_CACHE[key]
        else:
            _COLUMN_TYPE_CACHE.pop(f"{database}.{table}", None)


def _get_column_types(
    ch_client: clickhouse_connect.driver.Client,
    table: str,
    database: str = "tushare",
) -> dict[str, str]:
    """Lazy-load column types for a table with TTL-based per-process cache."""
    cache_key = f"{database}.{table}"
    now = time.monotonic()

    with _CACHE_LOCK:
        cached = _COLUMN_TYPE_CACHE.get(cache_key)
        if cached and cached[1] > now:
            return cached[0]

    result = ch_client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE database = '{database}' AND table = '{table}'"
    )
    type_map = {row[0]: row[1] for row in result.result_rows}
    expires_at = now + _CACHE_TTL

    with _CACHE_LOCK:
        _COLUMN_TYPE_CACHE[cache_key] = (type_map, expires_at)

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

        # 3. Fill None defaults for non-nullable columns (API returns None for some fields)
        for idx, field_name in enumerate(fields):
            if idx >= len(row) or row[idx] is not None:
                continue
            ch_type = column_types.get(field_name, "")
            if not ch_type or ch_type.startswith("Nullable(") or ch_type.startswith("LowCardinality"):
                continue
            # Non-nullable column with None value → fill sensible default
            if ch_type == "String":
                row[idx] = ""
            elif ch_type.startswith(("Int", "Float", "Decimal")):
                row[idx] = 0
            elif ch_type == "Date":
                row[idx] = _EPOCH_DATE

        # 4. Cast non-string values to string for String/LowCardinality columns
        for idx, field_name in enumerate(fields):
            if idx >= len(row) or row[idx] is None:
                continue
            ch_type = column_types.get(field_name, "")
            base_type = ch_type
            if base_type.startswith("Nullable("):
                base_type = base_type[len("Nullable("):-1]
            if base_type == "String" or base_type.startswith("LowCardinality"):
                if not isinstance(row[idx], str):
                    row[idx] = str(row[idx])

        normalized.append(row)

    return normalized
