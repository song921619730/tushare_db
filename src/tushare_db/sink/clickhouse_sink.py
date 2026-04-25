"""ClickHouse sink: write rows to ClickHouse tables.

Features:
- async_insert enabled by default (config.xml sets server-level)
- Native protocol (port 9000) for 2-3x write throughput vs HTTP
- ReplacingMergeTree(_version) ensures idempotent replays
"""

from __future__ import annotations

import time
from typing import Any

import clickhouse_connect
import clickhouse_connect.driver
import structlog

logger = structlog.get_logger()

# Async insert settings (also set server-side in config.xml)
ASYNC_INSERT_SETTINGS = {
    "async_insert": 1,
    "wait_for_async_insert": 1,
    "async_insert_max_data_size": 10485760,
    "async_insert_busy_timeout_ms": 200,
}


def get_native_client(
    host: str = "localhost",
    port: int = 8123,
    user: str = "pipeline",
    password: str = "",
    database: str = "tushare",
) -> clickhouse_connect.driver.Client:
    """Create a ClickHouse client for data operations.

    Note: clickhouse_connect >= 0.15 uses HTTP-only; native protocol was removed.
    """
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        database=database,
    )


def insert_rows(
    client: clickhouse_connect.driver.Client,
    table: str,
    columns: list[str],
    rows: list[list[Any]],
    database: str = "tushare",
) -> int:
    """Insert rows into a ClickHouse table.

    Args:
        client: ClickHouse Native client.
        table: Table name (without database prefix).
        columns: Column names in order.
        rows: List of row values (each row is a list matching columns order).
        database: Database name.

    Returns:
        Number of rows inserted.
    """
    if not rows:
        return 0

    start = time.monotonic()

    client.insert(
        table=table,
        data=rows,
        column_names=columns,
        settings=ASYNC_INSERT_SETTINGS,
        database=database,
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.debug(
        "insert_complete",
        table=f"{database}.{table}",
        rows=len(rows),
        duration_ms=elapsed_ms,
    )

    return len(rows)


def insert_with_version(
    client: clickhouse_connect.driver.Client,
    table: str,
    columns: list[str],
    rows: list[list[Any]],
    database: str = "tushare",
) -> int:
    """Insert rows with _version column automatically set to current timestamp in ms."""
    version = int(time.time() * 1000)

    # Ensure _version is in columns
    if "_version" not in columns:
        columns = columns + ["_version"]

    # Append version to each row
    versioned_rows = [row + [version] for row in rows]

    return insert_rows(client, table, columns, versioned_rows, database)
