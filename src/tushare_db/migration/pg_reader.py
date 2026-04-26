"""PostgreSQL reader: stream rows via server-side cursor."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg


@contextmanager
def pg_connection():
    """Yield a read-only PG connection from environment variables."""
    with psycopg.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", "5432")),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        dbname=os.environ["PG_DB"],
        autocommit=False,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        yield conn


def iter_pg_rows(
    conn,
    table: str,
    columns: list[str],
    batch_size: int = 100_000,
    where: str | None = None,
    order_by: str | None = None,
) -> Iterator[list[tuple]]:
    """Stream rows in batches via server-side cursor.

    Yields list of tuples, each tuple in `columns` order.
    """
    cols_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f"SELECT {cols_sql} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    with conn.cursor(name=f"migrate_{table}") as cur:
        cur.itersize = batch_size
        cur.execute(sql)

        batch = []
        for row in cur:
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def iter_partitioned_table(
    conn,
    spec,
    columns: list[str],
) -> Iterator[tuple[str, list[tuple]]]:
    """For partitioned PG tables, yield (partition_name, batch) pairs.

    Iterates partitions in chronological order: _2020, _2021, ..., _default last.
    """
    partition_tables = []
    for year in spec.partition_years:
        partition_tables.append(spec.partition_pattern.format(year=year))
    if spec.include_default_partition:
        partition_tables.append(f"{spec.pg_table}_default")

    for partition in partition_tables:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = %s LIMIT 1",
                (partition,),
            )
            if not cur.fetchone():
                continue
            cur.execute(f"SELECT count(*) FROM {partition}")
            row_count = cur.fetchone()[0]
            if row_count == 0:
                continue

        for batch in iter_pg_rows(
            conn,
            partition,
            columns,
            batch_size=spec.batch_size,
            order_by=f"ts_code, {spec.date_column}" if (spec.date_column and "ts_code" in columns) else (spec.date_column if spec.date_column else None),
        ):
            yield partition, batch


def check_partition_duplicates(conn, spec) -> dict[str, int]:
    """Cross-partition duplicate row pre-check.

    Returns {partition_name: duplicate_row_count}.
    """
    if not spec.partitioned or not spec.include_default_partition:
        return {}

    date_col = spec.date_column or "trade_date"
    primary_key = f"ts_code, {date_col}"
    results = {}

    # Only check last 2 years (most likely to cross-partition)
    for year in spec.partition_years[-2:]:
        partition_a = spec.partition_pattern.format(year=year)
        partition_b = f"{spec.pg_table}_default"

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT count(*) FROM (
                    SELECT {primary_key} FROM {partition_a}
                    INTERSECT
                    SELECT {primary_key} FROM {partition_b}
                ) t
            """)
            dup = cur.fetchone()[0]
            if dup > 0:
                results[f"{partition_a} ∩ {partition_b}"] = dup

    return results


def get_pg_table_columns(conn, table: str) -> list[str]:
    """Get column names for a PG table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        return [r[0] for r in cur.fetchall()]


def get_pg_table_types(conn, table: str) -> dict[str, str]:
    """Get column name → data type for a PG table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        return {r[0]: (r[1], r[2]) for r in cur.fetchall()}
