"""Bootstrap schemas: sample all enabled APIs, infer schemas, create tables.

Called during `tushare-db bootstrap`:
1. Sample all enabled interfaces from Tushare
2. Infer ClickHouse schemas from samples
3. CREATE 182 business tables in tushare database
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import clickhouse_connect.driver
import structlog
from dotenv import load_dotenv

from tushare_db.core.tushare_client import TushareClient
from tushare_db.config.loader import load_interface_specs
from tushare_db.schema.inferer import infer_schema
from tushare_db.schema.ddl_builder import build_create_table
from tushare_db.sink.clickhouse_sink import insert_rows

logger = structlog.get_logger()
load_dotenv()


def bootstrap_schemas(
    ch_client: clickhouse_connect.driver.Client,
    tushare_client: TushareClient,
    sample_dir: str = "data/samples",
    only: str | None = None,
) -> int:
    """Sample APIs, infer schemas, and create ClickHouse tables.

    Args:
        ch_client: ClickHouse Native client.
        tushare_client: Tushare API client.
        sample_dir: Directory to save/load sample JSON files.
        only: Comma-separated list of interfaces to process.

    Returns:
        Number of tables created.
    """
    sample_path = Path(sample_dir)
    sample_path.mkdir(parents=True, exist_ok=True)

    specs = load_interface_specs()

    if only:
        target_names = {n.strip() for n in only.split(",")}
        specs = [s for s in specs if s.name in target_names]
    else:
        specs = [s for s in specs if s.enabled]

    tables_created = 0

    for spec in specs:
        try:
            _process_spec(spec, tushare_client, ch_client, sample_path)
            tables_created += 1
            time.sleep(0.2)
        except Exception as e:
            logger.error(
                "Failed to bootstrap interface",
                interface=spec.name,
                error=str(e),
            )

    logger.info("Bootstrap complete", tables_created=tables_created)
    return tables_created


def _process_spec(
    spec,
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    sample_path: Path,
) -> None:
    """Process a single interface: sample, infer, create."""
    sample_file = sample_path / f"{spec.name}.json"

    # Step 1: Sample if not already done
    if not sample_file.exists():
        response = _sample_interface(tushare_client, spec)
        if response is None:
            logger.warning("Empty sample, skipping", interface=spec.name)
            return
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        logger.info("Sample saved", interface=spec.name, path=str(sample_file))

    # Step 2: Infer schema
    columns = infer_schema(
        sample_file,
        field_names=spec.fields or None,
        overrides=spec.schema_overrides or None,
    )

    # Step 3: Create table
    table_name = f"tushare.{spec.table}"
    ddl = build_create_table(
        table_name=table_name,
        columns=columns,
        partition_key=spec.partition_key or "tuple()",
        order_by=spec.order_by or "ts_code, trade_date",
    )

    ch_client.command(ddl)
    logger.info("Table created", interface=spec.name, table=table_name)


def _sample_interface(client: TushareClient, spec) -> dict | None:
    """Make a minimal API call for sampling."""
    strategy = spec.fetch_strategy.kind

    params: dict = {}
    if strategy in ("date_loop", "offset_paging"):
        params = {"trade_date": "20240101"}
    elif strategy == "period_loop":
        params = {"period": "20240331"}
    elif strategy == "per_symbol_period":
        params = {"ts_code": "000001.SZ", "period": "20240331"}
    elif strategy == "monthly_window":
        params = {"month": "202401"}

    return client.call(spec.name, bucket=spec.freq_bucket, **params)
