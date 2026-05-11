"""Build ClickHouse CREATE TABLE DDL from inferred schemas.

Features:
- ReplacingMergeTree(_version) for idempotency
- LowCardinality for ts_code/exchange
- Date CODEC(DoubleDelta, ZSTD(3))
- Float CODEC(Gorilla, ZSTD(3))
- Partition by trade_date/end_date/empty tuple
"""

from __future__ import annotations


DATE_CODEC = "CODEC(DoubleDelta, ZSTD(3))"
FLOAT_CODEC = "CODEC(Gorilla, ZSTD(3))"


def build_create_table(
    table_name: str,
    columns: list[tuple[str, str]],
    partition_key: str = "tuple()",
    order_by: str = "ts_code, trade_date",
) -> str:
    """Generate ClickHouse CREATE TABLE DDL.

    Args:
        table_name: Full table name (e.g., 'tushare.stock_daily').
        columns: List of (column_name, clickhouse_type) pairs.
        partition_key: PARTITION BY expression.
        order_by: ORDER BY columns.

    Returns:
        Complete CREATE TABLE SQL statement.
    """
    col_defs = []
    for col_name, col_type in columns:
        # Add CODEC hints for date/float columns
        codec = ""
        if col_type == "Date" and "date" in col_name.lower():
            codec = f" {DATE_CODEC}"
        elif col_type == "Float64" and any(x in col_name.lower() for x in ("price", "open", "close", "high", "low", "amount")):
            codec = f" {FLOAT_CODEC}"

        col_defs.append(f"    {col_name} {col_type}{codec}")

    ddl = (
        f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        + ",\n".join(col_defs)
        + f"\n) ENGINE = ReplacingMergeTree(_version)\n"
        f"PARTITION BY {partition_key}\n"
        f"ORDER BY ({order_by})"
    )

    return ddl


def build_create_tables_batch(
    tables: dict[str, tuple[list[tuple[str, str]], str, str]],
) -> list[str]:
    """Generate CREATE TABLE DDL for multiple tables.

    Args:
        tables: {table_name: (columns, partition_key, order_by)}.

    Returns:
        List of CREATE TABLE SQL statements.
    """
    return [
        build_create_table(name, columns, partition_key, order_by)
        for name, (columns, partition_key, order_by) in tables.items()
    ]
