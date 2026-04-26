#!/usr/bin/env python
"""Backfill income table for 20 stocks × 8 quarters.

Usage (inside pipeline-scheduler container):
    python scripts/backfill_income_8q.py
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

STOCKS = [
    "000001.SZ","000002.SZ","000063.SZ","000100.SZ","000157.SZ",
    "000333.SZ","000568.SZ","000651.SZ","000725.SZ","000858.SZ",
    "002304.SZ","002415.SZ","002594.SZ","002714.SZ","300059.SZ",
    "300750.SZ","600000.SH","600036.SH","600276.SH","600519.SH",
]

PERIODS = [
    "20230331","20230630","20230930","20231231",
    "20240331","20240630","20240930","20241231",
]


def main():
    ch = clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )
    tushare = TushareClient(token=os.environ.get("TUSHARE_TOKEN", ""))

    total_rows = 0
    total_calls = 0
    errors = 0

    for period in PERIODS:
        for ts in STOCKS:
            try:
                resp = tushare.call("income", ts_code=ts, period=period)
                total_calls += 1
                items = resp.get("data", {}).get("items", [])
                if not items:
                    continue
                fields = resp["data"]["fields"]

                # Normalize
                column_types = _get_column_types(ch, "tushare_income", database="tushare")
                normalized = _normalize_items(fields, items, column_types=column_types)

                # Write
                insert_with_version(ch, table="tushare_income", columns=fields, rows=normalized)
                total_rows += len(normalized)
                logger.info("Fetched", ts=ts, period=period, rows=len(normalized))
            except Exception as e:
                errors += 1
                logger.warning("Failed", ts=ts, period=period, error=str(e))
            time.sleep(0.15)

    logger.info("Complete", calls=total_calls, rows=total_rows, errors=errors)

    # Verify
    count = ch.query("SELECT count() FROM tushare.tushare_income FINAL").result_rows[0][0]
    logger.info("Income table row count", rows=count)

    # Verify B1: 贵州茅台 2023 营收
    result = ch.query(
        "SELECT ts_code, end_date, total_revenue FROM tushare.tushare_income FINAL "
        "WHERE ts_code='600519.SH' AND end_date='20231231' LIMIT 1"
    )
    if result.result_rows:
        row = result.result_rows[0]
        logger.info("B1 verification", ts_code=row[0], end_date=str(row[1]), total_revenue=row[2])

    ch.close()


if __name__ == "__main__":
    main()
