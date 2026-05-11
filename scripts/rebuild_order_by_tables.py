"""Rebuild ClickHouse tables that were created with ORDER BY tuple().

This script:
1. Reads the correct ORDER BY from YAML interface configs
2. For each affected table, creates a new table with correct ORDER BY
   (copying column definitions from the existing table)
3. Drops the old table
4. Resets sync_state for affected interfaces
5. Triggers backfill

Usage:
    python scripts/rebuild_order_by_tables.py --dry-run    # Preview changes
    python scripts/rebuild_order_by_tables.py --execute    # Actually execute
"""

from __future__ import annotations

import argparse
import os
import re

import clickhouse_connect

# 31 affected tables (confirmed in configs) with correct order_by from YAML configs
AFFECTED_TABLES = [
    ("tushare_fund_sales_ratio", "ts_code"),
    ("tushare_fund_sales_vol", "ts_code"),
    ("tushare_moneyflow_mkt_dc", "ts_code, trade_date"),
    ("tushare_cb_share", "ts_code, trade_date"),
    ("tushare_bse_mapping", "ts_code"),
    ("tushare_cb_call", "ts_code, ann_date"),
    ("tushare_cb_issue", "ts_code, ann_date"),
    ("tushare_fund_manager", "ts_code"),
    ("tushare_cn_pmi", "month"),
    ("tushare_us_tbr", "date"),
    ("tushare_us_trltr", "date"),
    ("tushare_us_tltr", "date"),
    ("tushare_us_trycr", "date"),
    ("tushare_us_tycr", "date"),
    ("tushare_wz_index", "month"),
    ("tushare_yc_cb", "ts_code, trade_date"),
    ("tushare_st", "ts_code, trade_date"),
    ("tushare_sf_month", "month"),
    ("tushare_shibor_quote", "shibor_date"),
    ("tushare_teleplay_record", "ts_code, report_date"),
    ("tushare_stk_account_old", "ts_code"),
    ("tushare_new_share", "ts_code"),
    ("tushare_fut_wsr", "ts_code, trade_date"),
    ("tushare_fut_holding", "ts_code, trade_date"),
    ("tushare_fut_weekly_detail", "symbol, date"),
    ("tushare_gz_index", "month"),
    ("tushare_hm_list", "ts_code"),
    ("tushare_eco_cal", "date"),
    ("tushare_report_rc", "ts_code, report_date"),
    ("tushare_index_classify", "ts_code"),
    ("tushare_fund_company", "ts_code"),
]


def get_ch_client():
    host = os.environ.get("CH_HOST", "localhost")
    port = int(os.environ.get("CH_HTTP_PORT", "8123"))
    password = os.environ.get("CH_PIPELINE_PASSWORD", "")
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username="pipeline",
        password=password,
        database="tushare",
        connect_timeout=10,
        send_receive_timeout=300,
    )


def extract_columns_from_ddl(ddl: str) -> list[tuple[str, str]]:
    """Extract column name, type pairs from SHOW CREATE TABLE result.

    Handles both single-line and multi-line DDL formats.
    ClickHouse returns DDL with literal \\n escapes, so we normalize first.
    """
    # Normalize literal \n to actual newlines
    ddl = ddl.replace("\\n", "\n")

    columns: list[tuple[str, str]] = []

    # Find the parentheses block containing column definitions
    start = ddl.index("(")
    # Find matching closing paren (account for nested parens in functions)
    depth = 0
    end = start
    for i, ch in enumerate(ddl[start:], start):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i
                break

    inner = ddl[start + 1:end]

    # Split by commas, but not inside parentheses
    parts = []
    depth = 0
    current = ""
    for ch in inner:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    for part in parts:
        part = part.strip()
        # Skip ENGINE, INDEX, CONSTRAINT, etc.
        if part.startswith(("INDEX", "CONSTRAINT", "PRIMARY KEY")):
            continue
        # Parse "col_name type" or "`col_name` type" or `col_name` type ...
        # Remove backticks for parsing
        clean = part.strip()
        if clean.startswith("`"):
            # Find closing backtick
            closing = clean.index("`", 1)
            col_name = clean[1:closing]
            rest = clean[closing + 1:].strip()
        else:
            tokens = clean.split(None, 1)
            if len(tokens) < 2:
                continue
            col_name = tokens[0]
            rest = tokens[1]

        # rest is the type (everything after the column name)
        if rest:
            columns.append((col_name, rest))

    return columns


def get_row_count(client, table: str) -> int:
    result = client.command(f"SELECT count() FROM tushare.{table}")
    return int(result)


def table_exists(client, table: str) -> bool:
    result = client.command(
        f"SELECT count() FROM system.tables WHERE database = 'tushare' AND name = '{table}'"
    )
    return int(result) > 0


def get_table_engine_info(client, table: str) -> dict:
    """Get ENGINE, PARTITION BY, ORDER BY, PRIMARY KEY from system.tables."""
    query = (
        f"SELECT engine, partition_key, sorting_key, primary_key, sampling_key "
        f"FROM system.tables "
        f"WHERE database = 'tushare' AND name = '{table}'"
    )
    result = client.query(query)
    if not result.result_rows:
        return {}
    row = result.result_rows[0]
    return {
        "engine": row[0],
        "partition_key": row[1],
        "sorting_key": row[2],
        "primary_key": row[3],
        "sampling_key": row[4],
    }


def rebuild_table(client, table: str, order_by: str, dry_run: bool = False) -> bool:
    """Rebuild a single table with correct ORDER BY."""
    print(f"\n--- Processing {table} ---")

    if not table_exists(client, table):
        print(f"  SKIP: Table does not exist")
        return False

    row_count = get_row_count(client, table)
    print(f"  Current row count: {row_count}")
    print(f"  New ORDER BY: ({order_by})")

    # Get existing DDL for column extraction
    existing_ddl = client.command(f"SHOW CREATE TABLE tushare.{table}")
    columns = extract_columns_from_ddl(existing_ddl)
    print(f"  Columns extracted: {len(columns)}")

    if len(columns) < 2:  # Should have at least 1 data column + _version
        print(f"  WARNING: Very few columns extracted, DDL may be malformed")
        print(f"  Raw DDL preview: {existing_ddl[:200]}")

    # Get engine info for PARTITION BY etc.
    engine_info = get_table_engine_info(client, table)
    partition_key = engine_info.get("partition_key", "tuple()")
    primary_key = engine_info.get("primary_key", "")

    if dry_run:
        col_defs = ", ".join(f"{name} {typ}" for name, typ in columns[:3])
        print(f"  [DRY RUN] Would DROP and CREATE with {len(columns)} columns")
        print(f"  [DRY RUN] Columns: {', '.join(c[0] for c in columns)}")
        print(f"  [DRY RUN] PARTITION BY: {partition_key}")
        print(f"  [DRY RUN] ORDER BY: ({order_by})")
        return True

    shadow = f"{table}_rebuild"
    old = f"{table}_old"

    try:
        # Clean up any leftover shadow tables
        client.command(f"DROP TABLE IF EXISTS {shadow}")
        client.command(f"DROP TABLE IF EXISTS {old}")

        # Build CREATE TABLE DDL
        col_defs = ",\n    ".join(f"`{name}` {typ}" for name, typ in columns)
        create_sql = (
            f"CREATE TABLE {shadow} (\n"
            f"    {col_defs}\n"
            f") ENGINE = ReplacingMergeTree(_version)\n"
        )

        if partition_key and partition_key != "":
            create_sql += f"PARTITION BY {partition_key}\n"

        if primary_key and primary_key != "":
            create_sql += f"PRIMARY KEY {primary_key}\n"

        create_sql += f"ORDER BY ({order_by})\n"

        print(f"  Creating shadow table...")
        client.command(create_sql)

        # Step 2: Copy data (for tables that actually have data)
        if row_count > 0:
            print(f"  Copying {row_count} rows...")
            client.command(f"INSERT INTO {shadow} SELECT * FROM {table}")

        # Step 3: Verify row count
        new_count = get_row_count(client, shadow)
        print(f"  Shadow row count: {new_count}")

        # Step 4: Atomic rename
        print(f"  Renaming tables...")
        client.command(f"RENAME TABLE {table} TO {old}, {shadow} TO {table}")

        # Step 5: Drop old table
        print(f"  Dropping old table...")
        client.command(f"DROP TABLE IF EXISTS {old}")

        # Step 6: Verify new ORDER BY
        new_engine_info = get_table_engine_info(client, table)
        actual_sorting = new_engine_info.get("sorting_key", "")
        print(f"  Verified ORDER BY: {actual_sorting}")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        # Cleanup
        try:
            client.command(f"DROP TABLE IF EXISTS {shadow}")
        except Exception:
            pass
        raise


def reset_sync_state(client, dry_run: bool = False):
    """Reset sync_state for all affected interfaces."""
    interfaces = []
    for table, _ in AFFECTED_TABLES:
        if table.startswith("tushare_"):
            interfaces.append(table[len("tushare_"):])

    print(f"\n--- Resetting sync_state for {len(interfaces)} interfaces ---")

    for interface in interfaces:
        escaped = interface.replace("'", "''")
        alter_query = (
            f"ALTER TABLE _meta.sync_state DELETE "
            f"WHERE interface = '{escaped}'"
        )

        if dry_run:
            print(f"  [DRY RUN] {alter_query}")
        else:
            try:
                client.command(alter_query)
                print(f"  Deleted sync_state for {interface}")
            except Exception as e:
                print(f"  WARNING {interface}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Rebuild tables with correct ORDER BY")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Actually execute the rebuild")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        return

    dry_run = args.dry_run

    client = get_ch_client()

    print(f"{'[DRY RUN] ' if dry_run else ''}Rebuilding {len(AFFECTED_TABLES)} tables with correct ORDER BY")

    success = 0
    skipped = 0
    failed = 0
    for table, order_by in AFFECTED_TABLES:
        try:
            result = rebuild_table(client, table, order_by, dry_run=dry_run)
            if result is True:
                success += 1
            elif result is False:
                skipped += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary: {success} succeeded, {skipped} skipped, {failed} failed")

    if not dry_run:
        reset_sync_state(client, dry_run=False)
        print("\nDone! Tables rebuilt. Run backfill to repopulate data.")
    else:
        reset_sync_state(client, dry_run=True)


if __name__ == "__main__":
    main()
