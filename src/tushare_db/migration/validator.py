"""Validator: three-layer migration verification (row count / sample / aggregates)."""

from __future__ import annotations

import structlog

logger = structlog.get_logger()


def validate_row_count(pg_conn, ch_client, spec) -> dict:
    """Layer 1: Compare row counts between PG and CH."""
    pg_count = _pg_total_rows(pg_conn, spec)
    ch_count = _ch_count(ch_client, spec)

    return {
        "layer": "row_count",
        "pg_count": pg_count,
        "ch_count": ch_count,
        "diff": ch_count - pg_count,
        "passed": ch_count == pg_count,
    }


def _pg_total_rows(spec) -> int:
    """Sum rows across all partitions (or single table)."""
    from tushare_db.migration.pg_reader import pg_connection

    with pg_connection() as conn:
        if not spec.partitioned:
            with conn.cursor() as cur:
                cur.execute(f"SELECT count(*) FROM {spec.pg_table}")
                return cur.fetchone()[0]

        total = 0
        for year in spec.partition_years:
            partition = spec.partition_pattern.format(year=year)
            with conn.cursor() as cur:
                try:
                    cur.execute(f"SELECT count(*) FROM {partition}")
                    total += cur.fetchone()[0]
                except Exception:
                    continue
        if spec.include_default_partition:
            with conn.cursor() as cur:
                try:
                    cur.execute(f"SELECT count(*) FROM {spec.pg_table}_default")
                    total += cur.fetchone()[0]
                except Exception:
                    pass
        return total


def _ch_count(ch_client, spec) -> int:
    result = ch_client.query(
        f"SELECT count() FROM {spec.ch_database}.{spec.ch_table} FINAL"
    )
    return int(result.result_rows[0][0])


def validate_sample(pg_conn, ch_client, spec, sample_size: int = 100) -> dict:
    """Layer 2: Random sample by primary key, compare cells."""
    if not spec.date_column:
        return {"layer": "sample", "passed": True, "total": 0, "skipped": "no date column"}

    from tushare_db.migration.pg_reader import get_pg_table_columns

    # Get PG columns (exclude created_at/updated_at)
    pg_cols = get_pg_table_columns(pg_conn, spec.pg_table)
    data_cols = [c for c in pg_cols if c not in ("created_at", "updated_at")]

    if spec.partitioned:
        source = f"{spec.pg_table}_{spec.partition_years[-1]}"
    else:
        source = spec.pg_table

    # Sample keys
    with pg_conn.cursor() as cur:
        cur.execute(f"""
            SELECT ts_code, {spec.date_column}
            FROM {source}
            ORDER BY random()
            LIMIT {sample_size}
        """)
        keys = cur.fetchall()

    mismatches = []
    for ts_code, date_val in keys:
        # Fetch from PG
        pg_row = _fetch_row(pg_conn, source, ts_code, date_val, spec.date_column, data_cols)
        # Fetch from CH
        ch_row = _fetch_row_ch(ch_client, spec, ts_code, date_val, spec.date_column, data_cols)
        if pg_row and ch_row:
            for i, col in enumerate(data_cols):
                pg_val = pg_row[i]
                ch_val = ch_row[i]
                if pg_val is None and ch_val is None:
                    continue
                if pg_val is None or ch_val is None:
                    mismatches.append({"ts_code": ts_code, "col": col, "pg": pg_val, "ch": ch_val})
                    break
                # Numeric comparison with tolerance
                if isinstance(pg_val, (int, float)) and isinstance(ch_val, (int, float)):
                    from tushare_db.migration.field_resolver import should_normalize
                    scale = 10_000 if should_normalize(col, spec.pg_table) else 1
                    expected = float(pg_val) * scale
                    if abs(float(ch_val) - expected) / max(abs(expected), 1) > 0.0001:
                        mismatches.append({"ts_code": ts_code, "col": col, "pg": pg_val, "ch": ch_val})
                        break
                elif pg_val != ch_val:
                    mismatches.append({"ts_code": ts_code, "col": col, "pg": pg_val, "ch": ch_val})
                    break

    return {
        "layer": "sample", "total": len(keys), "passed": len(mismatches) == 0,
        "mismatches": mismatches[:10],
    }


def _fetch_row(pg_conn, table, ts_code, date_val, date_col, columns):
    with pg_conn.cursor() as cur:
        cols = ", ".join(f'"{c}"' for c in columns)
        cur.execute(
            f"SELECT {cols} FROM {table} WHERE ts_code=%s AND {date_col}=%s",
            (ts_code, date_val),
        )
        return cur.fetchone()


def _fetch_row_ch(ch_client, spec, ts_code, date_val, date_col, columns):
    cols = ", ".join(columns)
    result = ch_client.query(
        f"SELECT {cols} FROM {spec.ch_database}.{spec.ch_table} FINAL "
        f"WHERE ts_code='{ts_code}' AND {date_col}='{date_val}'"
    )
    if result.result_rows:
        return result.result_rows[0]
    return None


def validate_aggregates(pg_conn, ch_client, spec, numeric_cols: list[str]) -> dict:
    """Layer 3: Aggregate (sum, min, max) comparison for numeric columns."""
    from tushare_db.migration.field_resolver import should_normalize

    results = []
    for col in numeric_cols:
        with pg_conn.cursor() as cur:
            cur.execute(f"SELECT sum({col}), min({col}), max({col}) FROM {spec.pg_table}")
            pg_sum, pg_min, pg_max = cur.fetchone()

        ch_result = ch_client.query(
            f"SELECT sum({col}), min({col}), max({col}) "
            f"FROM {spec.ch_database}.{spec.ch_table} FINAL"
        )
        ch_sum, ch_min, ch_max = ch_result.result_rows[0]

        scale = 10_000 if should_normalize(col, spec.pg_table) else 1
        expected_sum = float(pg_sum or 0) * scale
        diff_pct = abs(float(ch_sum or 0) - expected_sum) / max(abs(expected_sum), 1)

        results.append({
            "col": col,
            "pg_sum": pg_sum, "ch_sum": ch_sum, "scale": scale,
            "diff_pct": diff_pct,
            "passed": diff_pct < 0.01,  # < 1% tolerance for aggregates
        })

    return {
        "layer": "aggregate", "cols": results,
        "passed": all(r["passed"] for r in results),
    }


def _get_numeric_columns(ch_client, spec) -> list[str]:
    """Get numeric column names from CH table schema."""
    result = ch_client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE database='{spec.ch_database}' AND table='{spec.ch_table}' "
        f"AND type IN ('Float64', 'Int32', 'Int64', 'Decimal64(2)', 'Decimal64(4)')"
    )
    return [r[0] for r in result.result_rows]


def validate_table(pg_conn, ch_client, spec) -> bool:
    """Run all three validation layers on a single table."""
    r1 = validate_row_count(pg_conn, ch_client, spec)
    logger.info("row_count_validation", table=spec.ch_table, **r1)
    if not r1["passed"]:
        logger.error("row_count_mismatch", **r1)
        return False

    r2 = validate_sample(pg_conn, ch_client, spec)
    logger.info("sample_validation", table=spec.ch_table, **r2)
    if not r2["passed"]:
        logger.error("sample_mismatch", **r2)
        return False

    numeric_cols = _get_numeric_columns(ch_client, spec)
    if numeric_cols:
        r3 = validate_aggregates(pg_conn, ch_client, spec, numeric_cols)
        logger.info("aggregate_validation", table=spec.ch_table, passed=r3["passed"])
        if not r3["passed"]:
            logger.error("aggregate_mismatch", **r3)
            return False

    return True
