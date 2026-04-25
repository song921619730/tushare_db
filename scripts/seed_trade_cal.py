"""Seed trade_cal table from Tushare API.

Called during bootstrap to populate the trading calendar before any
date_loop or period_loop work units can be planned.
"""

from __future__ import annotations

import os

import clickhouse_connect.driver
import structlog
from dotenv import load_dotenv

from tushare_db.core.tushare_client import TushareClient
from tushare_db.sink.clickhouse_sink import insert_rows

logger = structlog.get_logger()
load_dotenv()


def seed_trade_cal(
    ch_client: clickhouse_connect.driver.Client,
    tushare_client: TushareClient,
) -> int:
    """Fetch and seed the trade_cal table.

    Returns:
        Number of rows seeded.
    """
    logger.info("Seeding trade_cal table")

    # Create table if not exists
    ch_client.command(
        "CREATE TABLE IF NOT EXISTS _meta.trade_cal ("
        "    exchange  LowCardinality(String),"
        "    cal_date  Date,"
        "    is_open   UInt8,"
        "    pre_trade_date Date,"
        "    _version  UInt64"
        ") ENGINE = ReplacingMergeTree(_version) "
        "PARTITION BY tuple() "
        "ORDER BY (exchange, cal_date)"
    )

    # Fetch from Tushare
    response = tushare_client.call("trade_cal", bucket="normal", exchange="SSE")
    fields = response.get("data", {}).get("fields", [])
    items = response.get("data", {}).get("items", [])

    if not items:
        logger.warning("No trade_cal data received from Tushare")
        return 0

    # Normalize dates
    normalized = _normalize_items(fields, items)

    # Insert into ClickHouse
    insert_rows(
        ch_client,
        table="trade_cal",
        columns=fields,
        rows=normalized,
        database="_meta",
    )

    logger.info("Trade_cal seeded", rows=len(items))
    return len(items)


def _normalize_items(fields: list[str], items: list[list]) -> list[list]:
    """Normalize date strings for ClickHouse Date type."""
    from datetime import datetime

    date_indices = [i for i, f in enumerate(fields) if "date" in f.lower()]
    normalized = []
    for item in items:
        row = list(item)
        for idx in date_indices:
            if idx < len(row) and row[idx] and isinstance(row[idx], str):
                val = row[idx].strip()
                if len(val) == 8 and val.isdigit():
                    row[idx] = datetime.strptime(val, "%Y%m%d").date()
        normalized.append(row)
    return normalized
