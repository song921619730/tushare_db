#!/usr/bin/env python
"""Backfill financial tables for all stocks across 8+ quarters.

Usage:
    python scripts/backfill_financials.py

This script:
1. Gets ts_codes from tushare_stock_daily
2. For each ts_code, calls income/balancesheet/cashflow/fina_indicator
   APIs for each quarter from 2023Q1 to 2024Q4
3. Writes results to ClickHouse
"""

from __future__ import annotations

import os
import time

import clickhouse_connect
import structlog

from tushare_db.core.tushare_client import TushareClient
from tushare_db.sink.clickhouse_sink import insert_with_version
from tushare_db.runner.worker import _get_column_types, _normalize_items

logger = structlog.get_logger()

# Fiscal quarters to backfill (8 quarters from 2023Q1 to 2024Q4)
PERIODS = [
    "20230331", "20230630", "20230930", "20231231",
    "20240331", "20240630", "20240930", "20241231",
]

# Financial interfaces to backfill
INTERFACES = ["income", "balancesheet", "cashflow", "fina_indicator", "dividend"]

# Max stocks to backfill (None = all stocks in stock_daily)
MAX_STOCKS = 20


def get_ch_client() -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )


def get_stock_codes(ch) -> list[str]:
    """Get top N ts_codes from stock_daily table."""
    result = ch.query(
        "SELECT DISTINCT ts_code FROM tushare.tushare_stock_daily FINAL ORDER BY ts_code"
    )
    codes = [row[0] for row in result.result_rows]
    if MAX_STOCKS:
        codes = codes[:MAX_STOCKS]
    return codes


def main():
    ch_client = get_ch_client()
    tushare = TushareClient(token=os.environ.get("TUSHARE_TOKEN", ""))

    stock_codes = get_stock_codes(ch_client)
    logger.info(
        "Starting financial backfill",
        stocks=len(stock_codes),
        interfaces=INTERFACES,
        periods=len(PERIODS),
    )

    total_rows = 0
    total_calls = 0
    errors = 0

    for interface in INTERFACES:
        table_name = f"tushare_{interface}"
        for period in PERIODS:
            for ts_code in stock_codes:
                try:
                    resp = tushare.call(interface, ts_code=ts_code, period=period)
                    total_calls += 1

                    items = resp.get("data", {}).get("items", [])
                    if not items:
                        continue

                    fields = resp["data"]["fields"]

                    column_types = _get_column_types(ch_client, table_name, database="tushare")
                    normalized = _normalize_items(fields, items, column_types=column_types)

                    insert_with_version(ch_client, table=table_name, columns=fields, rows=normalized)
                    total_rows += len(normalized)
                    logger.info(
                        "Fetched",
                        interface=interface,
                        ts_code=ts_code,
                        period=period,
                        rows=len(normalized),
                    )
                except Exception as e:
                    errors += 1
                    logger.warning(
                        "Failed",
                        interface=interface,
                        ts_code=ts_code,
                        period=period,
                        error=str(e),
                    )

                time.sleep(0.15)

    logger.info("Financial backfill complete", calls=total_calls, rows=total_rows, errors=errors)

    # Verification
    for interface in INTERFACES:
        table_name = f"tushare_{interface}"
        count = ch_client.query(
            f"SELECT count() FROM tushare.{table_name} FINAL"
        ).result_rows[0][0]
        logger.info("Table row count", table=table_name, rows=count)

    # B1: 600519.SH 2023 total_revenue verification (income table only)
    result = ch_client.query(
        "SELECT ts_code, end_date, total_revenue FROM tushare.tushare_income FINAL "
        "WHERE ts_code='600519.SH' AND end_date='20231231' LIMIT 1"
    )
    if result.result_rows:
        row = result.result_rows[0]
        logger.info("B1 verification", ts_code=row[0], end_date=str(row[1]), total_revenue=row[2])

    ch_client.close()
    tushare.close()


if __name__ == "__main__":
    main()
