"""Bootstrap: create _meta tables and initialize the tushare database.

PR1: Only creates _meta.{sync_state, sync_runs, api_calls} and empty tushare database.
Business table DDL is deferred to PR2 (sample → infer → CREATE).
"""

from __future__ import annotations

import clickhouse_connect
import structlog

logger = structlog.get_logger()

META_TABLES_DDL = {
    "sync_state": """
CREATE TABLE IF NOT EXISTS _meta.sync_state (
    interface         LowCardinality(String),
    scope_key         String,
    status            Enum8('pending'=0, 'running'=1, 'done'=2, 'partial'=3, 'failed'=4, 'biz_err'=5),
    rows              UInt64,
    last_success_at   DateTime64(3, 'Asia/Shanghai'),
    heartbeat_at      DateTime64(3, 'Asia/Shanghai'),
    attempts          UInt8,
    last_error        String,
    _version          UInt64
) ENGINE = ReplacingMergeTree(_version)
ORDER BY (interface, scope_key)
""",
    "sync_runs": """
CREATE TABLE IF NOT EXISTS _meta.sync_runs (
    run_id            UUID,
    interface         LowCardinality(String),
    batch             LowCardinality(String),
    scope             String,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    finished_at       Nullable(DateTime64(3, 'Asia/Shanghai')),
    units_total       UInt32,
    units_done        UInt32,
    units_failed      UInt32,
    status            Enum8('running'=1, 'done'=2, 'partial'=3, 'failed'=4),
    normalize_version UInt16
) ENGINE = MergeTree
ORDER BY (started_at, interface)
""",
    "api_calls": """
CREATE TABLE IF NOT EXISTS _meta.api_calls (
    run_id            UUID,
    interface         LowCardinality(String),
    params_hash       UInt64,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    duration_ms       UInt32,
    status            UInt16,
    rows              UInt32,
    error_msg         String
) ENGINE = MergeTree
ORDER BY (started_at, interface)
TTL toDate(started_at) + INTERVAL 90 DAY
""",
}


def get_client(
    host: str = "localhost",
    http_port: int = 8123,
    user: str = "pipeline",
    password: str = "",
) -> clickhouse_connect.driver.Client:
    """Create a ClickHouse HTTP client (clickhouse_connect uses HTTP by default)."""
    return clickhouse_connect.get_client(
        host=host,
        port=http_port,
        username=user,
        password=password,
    )


def init_meta(client: clickhouse_connect.driver.Client) -> None:
    """Create _meta database and all three metadata tables."""
    logger.info("Creating _meta database and tables")

    client.command("CREATE DATABASE IF NOT EXISTS _meta")
    logger.info("Database _meta created")

    for table_name, ddl in META_TABLES_DDL.items():
        client.command(ddl)
        logger.info(f"Table _meta.{table_name} created")

    logger.info("_meta initialization complete", tables=list(META_TABLES_DDL.keys()))


def init_tushare_db(client: clickhouse_connect.driver.Client) -> None:
    """Create empty tushare database (no business tables)."""
    client.command("CREATE DATABASE IF NOT EXISTS tushare")
    logger.info("Database tushare created (empty, business tables deferred to PR2)")


def verify_init(client: clickhouse_connect.driver.Client) -> None:
    """Verify that _meta tables exist after init."""
    tables = client.command(
        "SELECT name FROM system.tables WHERE database = '_meta' ORDER BY name"
    )
    expected = {"api_calls", "sync_runs", "sync_state"}
    actual = set(tables.split("\n")) if tables else set()

    missing = expected - actual
    if missing:
        raise RuntimeError(f"Missing _meta tables: {missing}")

    logger.info("Verification passed", tables=sorted(actual))
