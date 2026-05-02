"""Writer: batch write PG rows to ClickHouse with _version."""

from __future__ import annotations

from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from tushare_db.sink.clickhouse_sink import insert_rows
from tushare_db.migration.field_resolver import normalize_row
from tushare_db.migration.version_calc import calc_version

logger = structlog.get_logger()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def write_batch(
    ch_client,
    table: str,
    database: str,
    pg_columns: list[str],
    ch_columns: list[str],
    pg_rows: list[tuple],
    full_pg_row_dicts: list[dict],
    table_name: str = "",
) -> int:
    """Convert PG rows → CH rows, attach _version, insert.

    Args:
        ch_client: ClickHouse client.
        table: CH table name (without db prefix).
        database: CH database name.
        pg_columns: PG column names (used for normalize_value check).
        ch_columns: CH column names (may differ from pg_columns due to renames).
        pg_rows: List of PG row tuples (in pg_columns order).
        full_pg_row_dicts: Full row dicts with updated_at/created_at for version calc.
        table_name: Table name for normalization rules.

    Returns:
        Number of rows inserted.
    """
    col_index = {col: i for i, col in enumerate(pg_columns)}

    ch_rows: list[list[Any]] = []
    for pg_row, full_dict in zip(pg_rows, full_pg_row_dicts):
        sub_row = tuple(pg_row[col_index[c]] for c in pg_columns)
        normalized = normalize_row(sub_row, pg_columns, table_name=table_name)
        version = calc_version(full_dict)
        ch_rows.append(list(normalized) + [version])

    columns_with_version = ch_columns + ["_version"]

    inserted = insert_rows(
        ch_client,
        table=table,
        columns=columns_with_version,
        rows=ch_rows,
        database=database,
    )

    logger.info(
        "batch_written",
        table=f"{database}.{table}",
        rows=inserted,
    )
    return inserted
