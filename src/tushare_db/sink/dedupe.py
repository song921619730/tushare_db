"""Deduplication helper for ReplacingMergeTree tables."""

from __future__ import annotations

import clickhouse_connect.driver
import structlog

logger = structlog.get_logger()


def deduplicate_table(
    client: clickhouse_connect.driver.Client,
    table: str,
    database: str = "tushare",
) -> None:
    """Trigger OPTIMIZE TABLE FINAL to materialize ReplacingMergeTree dedup.

    This is expensive and should only be called for small reference tables
    or during scheduled maintenance, not during daily incremental writes.
    """
    logger.info("Starting dedup", table=f"{database}.{table}")
    client.command(f"OPTIMIZE TABLE {database}.{table} FINAL")
    logger.info("Dedup complete", table=f"{database}.{table}")
