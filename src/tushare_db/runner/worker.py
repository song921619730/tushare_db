"""Worker: execute a single work unit with heartbeat tracking and optional verification hook.

Each worker:
1. Marks unit as 'running' in _meta.sync_state with initial heartbeat
2. Fetches data from Tushare API
3. Writes to ClickHouse
4. Runs verify hook (if provided) — retries up to 2 times on failure
5. Updates _meta.sync_state to 'done'
6. Heartbeats every 30s during execution
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from collections.abc import Callable
from datetime import date, datetime, timezone

import clickhouse_connect
import clickhouse_connect.driver
import structlog

from tushare_db.planner.strategies import WorkUnit
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.errors import TushareBizError, TushareAuthError, TushareError
from tushare_db.sink.clickhouse_sink import insert_with_version
from tushare_db.schema.type_map import normalize_value
from tushare_db.schema.evolver import evolve_schema, parse_missing_columns

logger = structlog.get_logger()

# Verify hook signature: (ch_client, unit, rows_written) -> bool
# Returns True if verification passes, False triggers retry.
VerifyHook = Callable[
    ["clickhouse_connect.driver.Client", WorkUnit, int],
    bool,
]

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


def _delete_written_rows(
    ch_client: clickhouse_connect.driver.Client,
    table: str,
    params: dict,
) -> None:
    """Delete rows for a unit's scope so a verify-retry starts clean."""
    conditions = []
    if "ts_code" in params:
        conditions.append(f"ts_code = '{params['ts_code']}'")
    for date_key in ("trade_date", "end_date", "ann_date", "nav_date", "float_date"):
        if date_key in params:
            val = params[date_key]
            if isinstance(val, str) and len(val) == 8 and val.isdigit():
                conditions.append(f"{date_key} = '{val[:4]}-{val[4:6]}-{val[6:]}'")
            else:
                conditions.append(f"{date_key} = '{val}'")
            break
    if "period" in params:
        period = params["period"]
        if isinstance(period, str) and len(period) == 8:
            conditions.append(
                f"toYYYYMM(end_date) = {int(period[:4]) * 100 + int(period[4:6])}"
            )

    where = " AND ".join(conditions) if conditions else "1=0"
    if where and where != "1=0":
        try:
            ch_client.command(f"ALTER TABLE {table} DELETE WHERE {where}")
        except Exception:
            logger.debug("Cleanup delete skipped", table=table)


def _new_ch_client(database: str = "tushare") -> clickhouse_connect.driver.Client:
    """Create a new ClickHouse client from environment configuration."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database=database,
        connect_timeout=10,
        send_receive_timeout=300,
    )


def execute_unit(
    unit: WorkUnit,
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID,
    verify_hook: VerifyHook | None = None,
) -> int:
    """Execute a single work unit end-to-end.

    Args:
        verify_hook: Optional callback(ch_client, unit, rows_written) -> bool.
            Called after data is written. Returns False to trigger retry
            (re-fetch + re-write, up to 2 additional attempts).

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
    heartbeat_thread: threading.Thread | None = None

    try:
        _heartbeat_once(heartbeat_client, unit, attempt)

        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(heartbeat_client, unit, attempt, stop_event),
            daemon=True,
        )
        heartbeat_thread.start()

        # Fetch + write with optional verify-retry loop
        max_verify_retries = 2 if verify_hook else 0
        for retry in range(1 + max_verify_retries):
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

            # Write to ClickHouse with auto schema evolution on missing columns
            _insert_with_evolve(
                ch_client,
                table=unit.table,
                columns=fields,
                rows=normalized_items,
                raw_items=items,
            )

            rows_written = len(normalized_items)

            # Verify hook — retry if verification fails
            if verify_hook is not None:
                if not verify_hook(ch_client, unit, rows_written):
                    if retry < max_verify_retries:
                        logger.warning(
                            "Verify failed, retrying fetch",
                            interface=unit.interface,
                            scope_key=unit.scope_key,
                            attempt=retry + 1,
                        )
                        # Delete the just-written rows so retry starts clean
                        _delete_written_rows(ch_client, unit.table, unit.params)
                        continue
                    else:
                        logger.error(
                            "Verify failed after all retries",
                            interface=unit.interface,
                            scope_key=unit.scope_key,
                        )
                        mark_failed(ch_client, unit, "verify_failed", attempt)
                        return -5
                # Hook passed — data is good
                mark_done(ch_client, unit, rows_written, attempt)
                logger.info(
                    "Unit complete",
                    interface=unit.interface,
                    scope_key=unit.scope_key,
                    rows=rows_written,
                )
                return rows_written
            else:
                # No verify hook — mark done and exit
                mark_done(ch_client, unit, rows_written, attempt)
                logger.info(
                    "Unit complete",
                    interface=unit.interface,
                    scope_key=unit.scope_key,
                    rows=rows_written,
                )
                return rows_written

        # Should not reach here (all verify retries exhausted)
        return -5

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
        if heartbeat_thread is not None:
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


def _insert_with_evolve(
    ch_client: clickhouse_connect.driver.Client,
    table: str,
    columns: list[str],
    rows: list[list],
    raw_items: list[list],
) -> None:
    """Write to ClickHouse with automatic schema evolution on missing columns."""
    try:
        insert_with_version(
            ch_client,
            table=table,
            columns=columns,
            rows=rows,
        )
    except Exception as insert_err:
        missing = parse_missing_columns(str(insert_err))
        if not missing:
            raise
        logger.warning("Auto-evolving schema", table=table, missing=missing)
        # Infer types from sample rows; fallback to Nullable(String)
        desired = [(c, "Nullable(String)") for c in missing]
        evolve_schema(ch_client, database="tushare", table=table, desired_columns=desired)
        invalidate_column_cache(database="tushare", table=table)
        # Re-normalize with updated column types + retry
        column_types = _get_column_types(ch_client, table)
        normalized = _normalize_items(columns, raw_items, column_types=column_types)
        insert_with_version(
            ch_client,
            table=table,
            columns=columns,
            rows=normalized,
        )


def _normalize_items(
    fields: list[str],
    items: list[list],
    column_types: dict[str, str] | None = None,
) -> list[list]:
    """Normalize values: dates + 万元→元 + 万份→份."""
    normalized = []
    column_types = column_types or {}

    # Build indices for Date/DateTime columns from column_types (more accurate than name heuristic)
    date_type_indices: set[int] = set()
    datetime_type_indices: set[int] = set()
    for idx, field_name in enumerate(fields):
        ch_type = column_types.get(field_name, "")
        base_type = ch_type
        if base_type.startswith("Nullable("):
            base_type = base_type[len("Nullable("):-1]
        if base_type == "Date":
            date_type_indices.add(idx)
        elif base_type in ("DateTime", "DateTime64"):
            datetime_type_indices.add(idx)

    # Also use name heuristic as fallback (for tables where column_types isn't populated yet)
    name_date_indices = {i for i, f in enumerate(fields) if "date" in f.lower()}

    # Combined: type-based + name-based, excluding DateTime columns
    # (name heuristic would incorrectly catch DateTime columns like trade_date)
    all_date_indices = date_type_indices | (name_date_indices - datetime_type_indices)

    for item in items:
        row = list(item)

        # 1. Date normalization — handle YYYYMMDD, YYYYMM, YYYY, YYYY-MM-DD, YYYY/MM/DD formats
        for idx in all_date_indices:
            if idx >= len(row):
                continue
            val = row[idx]
            if val is None:
                continue
            if isinstance(val, str):
                val = val.strip()
                if not val:
                    row[idx] = None
                    continue
                try:
                    row[idx] = _parse_date_string(val)
                except (ValueError, TypeError):
                    row[idx] = None
            elif isinstance(val, datetime) and date_type_indices and idx in date_type_indices:
                row[idx] = val.date()

        # 1b. DateTime normalization — convert string dates / date objects to datetime for DateTime columns
        for idx in datetime_type_indices:
            if idx >= len(row) or row[idx] is None:
                continue
            val = row[idx]
            # Convert date → datetime (can happen when name heuristic fires before type info is known)
            if isinstance(val, date) and not isinstance(val, datetime):
                row[idx] = datetime(val.year, val.month, val.day)
                continue
            if not isinstance(val, str):
                continue
            val = val.strip()
            try:
                if len(val) == 8 and val.isdigit():
                    row[idx] = datetime.strptime(val, "%Y%m%d")
                elif "-" in val[:10]:
                    row[idx] = datetime.strptime(val[:19], "%Y-%m-%d %H:%M:%S")
                elif "/" in val[:10]:
                    row[idx] = datetime.strptime(val[:19], "%Y/%m/%d %H:%M:%S")
                elif "T" in val:
                    row[idx] = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                pass

        # 1c. Cap dates before ClickHouse epoch (1970-01-01)
        # ClickHouse Date stores days since epoch as UInt16 (0–65535), cannot represent pre-1970 dates.
        for idx in all_date_indices:
            if idx >= len(row) or row[idx] is None:
                continue
            val = row[idx]
            if isinstance(val, datetime):
                if val.year < 1970:
                    ch_type = column_types.get(fields[idx], "")
                    if ch_type.startswith("Nullable("):
                        row[idx] = None
                    else:
                        row[idx] = datetime(1970, 1, 1)
            elif isinstance(val, date) and not isinstance(val, datetime):
                if val.year < 1970:
                    ch_type = column_types.get(fields[idx], "")
                    if ch_type.startswith("Nullable("):
                        row[idx] = None
                    else:
                        row[idx] = _EPOCH_DATE

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

        # 3. Fill None/empty defaults for non-nullable columns (API returns None/empty for some fields)
        for idx, field_name in enumerate(fields):
            if idx >= len(row):
                continue
            val = row[idx]
            ch_type = column_types.get(field_name, "")
            if not ch_type or ch_type.startswith("Nullable("):
                continue
            # Treat empty strings and whitespace as None for typed columns
            if isinstance(val, str) and not val.strip():
                row[idx] = None
                val = None
            if val is not None:
                continue
            # Unwrap LowCardinality to determine base type for default value
            base_type = ch_type
            if base_type.startswith("LowCardinality("):
                base_type = base_type[len("LowCardinality("):-1]
            # Non-nullable column with None/empty value → fill sensible default
            if base_type == "String":
                row[idx] = ""
            elif base_type.startswith(("Int", "Float", "UInt", "Decimal")):
                row[idx] = 0
            elif base_type == "Date":
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


def _parse_date_string(val: str) -> datetime.date:
    """Parse a date string in various formats: YYYYMMDD, YYYYMM, YYYY, YYYY-MM-DD, YYYY/MM/DD, etc."""
    val = val.strip()
    if not val or val.lower() in {"-", "null", "none", "nan", "0000-00-00", "00000000"}:
        raise ValueError("empty/sentinel date string")

    if len(val) == 4 and val.isdigit():
        # YYYY → January 1st of that year
        return datetime(int(val), 1, 1).date()
    elif len(val) == 6 and val.isdigit():
        # YYYYMM → 1st of that month
        return datetime.strptime(val, "%Y%m").date()
    elif len(val) == 8 and val.isdigit():
        return datetime.strptime(val, "%Y%m%d").date()
    elif len(val) >= 10:
        # Try YYYY-MM-DD, YYYY/MM/DD, YYYY-MM-DD HH:MM:SS, YYYY/MM/DD HH:MM:SS
        clean = val[:10].replace("-", "").replace("/", "")
        if len(clean) >= 8 and clean[:8].isdigit():
            return datetime.strptime(clean[:8], "%Y%m%d").date()

    raise ValueError(f"unrecognized date format: {val}")
