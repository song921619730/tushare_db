#!/usr/bin/env python
"""Migration CLI: PostgreSQL → ClickHouse data migration.

Usage:
    uv run python scripts/migrate.py dry-run
    uv run python scripts/migrate.py run --priority P0 --confirm
    uv run python scripts/migrate.py run --only tushare_stock_basic --confirm
    uv run python scripts/migrate.py validate --priority P0
    uv run python scripts/migrate.py optimize --all
    uv run python scripts/migrate.py write-sync-state --all
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import click
import structlog

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import clickhouse_connect
import psycopg

from tushare_db.migration.registry import load_tables, filter_by_priority, TableSpec
from tushare_db.migration.pg_reader import (
    pg_connection, iter_partitioned_table, iter_pg_rows,
    check_partition_duplicates, get_pg_table_columns, get_pg_table_types,
)
from tushare_db.migration.field_resolver import resolve_columns, diff_fields, should_normalize
from tushare_db.migration.type_mapper import pg_type_to_ch
from tushare_db.migration.version_calc import verify_timezone_assumption
from tushare_db.migration.writer import write_batch
from tushare_db.migration.validator import validate_row_count, validate_table, validate_aggregates
from tushare_db.migration.state import (
    ensure_state_table, get_status, mark_running, mark_done, mark_failed,
)
from tushare_db.migration.sync_state_writer import write_sync_state_done

logger = structlog.get_logger()

REPORTS_DIR = Path(__file__).parent.parent / "docs" / "migration"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_ch_client():
    """Create ClickHouse client from environment."""
    import os
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_PORT", "8123")),
        username=os.environ.get("CH_PIPELINE_USER", "pipeline"),
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )


def _get_ch_columns(ch_client, database: str, table: str) -> list[str]:
    result = ch_client.query(
        f"SELECT name FROM system.columns "
        f"WHERE database='{database}' AND table='{table}' "
        f"ORDER BY position"
    )
    return [r[0] for r in result.result_rows]


@click.group()
def cli():
    """PostgreSQL → ClickHouse migration tool."""
    pass


@cli.command()
def dry_run():
    """Generate dry-run reports without writing data."""
    specs = load_tables()
    logger.info("dry_run_start", tables=len(specs))

    field_report = REPORTS_DIR / "field_diff_report.md"
    amount_report = REPORTS_DIR / "amount_conversion_report.md"
    dup_report = REPORTS_DIR / "partition_dup_check.md"

    field_lines = ["# Field Diff Report\n", f"Generated: {datetime.now(timezone.utc).isoformat()}\n"]
    amount_lines = ["# Amount Conversion Report\n", f"Generated: {datetime.now(timezone.utc).isoformat()}\n"]
    amount_lines += ["\n> ⚠️ Please review all tables before running with `--confirm`\n"]
    dup_lines = ["# Partition Duplicate Check\n", f"Generated: {datetime.now(timezone.utc).isoformat()}\n"]

    with pg_connection() as pg_conn:
        ch_client = get_ch_client()
        ensure_state_table(ch_client)

        for spec in specs:
            # Field diff
            pg_cols = get_pg_table_columns(pg_conn, spec.pg_table)
            try:
                ch_cols = _get_ch_columns(ch_client, spec.ch_database, spec.ch_table)
            except Exception:
                ch_cols = []
                field_lines.append(f"\n## {spec.pg_table} (⚠️ CH table does not exist)\n")
                field_lines.append(f"PG columns ({len(pg_cols)}): {', '.join(pg_cols)}\n")
                continue

            diff = diff_fields(pg_cols, ch_cols, spec.column_renames)
            field_lines.append(f"\n## {spec.pg_table}")
            field_lines.append(f"\n| both ({len(diff['both'])}) | {', '.join(diff['both'][:20])} |")
            if diff["pg_only_drop"]:
                field_lines.append(f"| pg_only_drop ({len(diff['pg_only_drop'])}) | {', '.join(diff['pg_only_drop'][:20])} |")
            if diff["ch_only_default"]:
                field_lines.append(f"| ch_only_default ({len(diff['ch_only_default'])}) | {', '.join(diff['ch_only_default'][:20])} |")

            # Amount conversion report
            cols_to_convert = [c for c in pg_cols if should_normalize(c, spec.pg_table)]
            if cols_to_convert:
                amount_lines.append(f"\n## {spec.pg_table}")
                amount_lines.append("| column | decision | reason |")
                amount_lines.append("|--------|----------|--------|")
                for col in cols_to_convert:
                    amount_lines.append(f"| {col} | x10000 | matches pattern |")
                for col in pg_cols:
                    if not should_normalize(col, spec.pg_table) and col not in ("created_at", "updated_at"):
                        amount_lines.append(f"| {col} | skip | not amount |")

            # Partition duplicate check
            if spec.partitioned:
                dups = check_partition_duplicates(pg_conn, spec)
                if dups:
                    dup_lines.append(f"\n## {spec.pg_table}")
                    for key, count in dups.items():
                        dup_lines.append(f"- **{key}**: {count} duplicates")
                    dup_lines.append("\n⚠️ **Please confirm before proceeding**\n")

    field_report.write_text("\n".join(field_lines), encoding="utf-8")
    amount_report.write_text("\n".join(amount_lines), encoding="utf-8")
    dup_report.write_text("\n".join(dup_lines), encoding="utf-8")

    logger.info("dry_run_done", reports=str(REPORTS_DIR))
    click.echo(f"[DRY-RUN] Complete. Reports in {REPORTS_DIR}")
    click.echo("   1. field_diff_report.md")
    click.echo("   2. amount_conversion_report.md")
    click.echo("   3. partition_dup_check.md")
    click.echo("Please review before running with --confirm")


@cli.command()
@click.option("--priority", default=None, help="P0/P1/P2/P3")
@click.option("--only", default=None, help="Migrate only this table")
@click.option("--confirm", is_flag=True, help="Confirm actual migration")
@click.option("--batch-size", default=None, help="Override batch size")
def run(priority, only, confirm, batch_size):
    """Run migration for specified tables."""
    if not confirm:
        click.echo("[WARN] Add --confirm to actually run migration")
        return

    specs = load_tables()
    if priority:
        specs = filter_by_priority(specs, priority)
    if only:
        specs = [s for s in specs if s.pg_table == only]

    if not specs:
        click.echo("No tables to migrate")
        return

    logger.info("migration_start", tables=len(specs))
    ch_client = get_ch_client()
    ensure_state_table(ch_client)

    # Timezone verification
    with pg_connection() as pg_conn:
        tz_ok = verify_timezone_assumption(pg_conn)
        if not tz_ok:
            click.echo("[WARN] Timezone verification failed! PG may be using UTC.")
            click.echo("Check version_calc.py _to_ms() timezone handling.")
            if not click.confirm("Continue anyway?", default=False):
                sys.exit(1)

    for spec in specs:
        _migrate_one(spec, ch_client)


@cli.command()
@click.option("--priority", default=None, help="P0/P1/P2/P3")
@click.option("--only", default=None, help="Validate only this table")
def validate(priority, only):
    """Run validation for migrated tables."""
    specs = load_tables()
    if priority:
        specs = filter_by_priority(specs, priority)
    if only:
        specs = [s for s in specs if s.pg_table == only]

    ch_client = get_ch_client()
    passed = 0
    failed = 0

    for spec in specs:
        status = get_status(ch_client, spec.pg_table)
        if status != "done":
            click.echo(f"SKIP {spec.pg_table} (status={status})")
            continue

        with pg_connection() as pg_conn:
            result = validate_table(pg_conn, ch_client, spec)
        if result:
            click.echo(f"PASS {spec.pg_table}")
            passed += 1
        else:
            click.echo(f"FAIL {spec.pg_table}")
            failed += 1

    click.echo(f"\nResults: {passed} passed, {failed} failed")


@cli.command()
@click.option("--all", "all_tables", is_flag=True, help="Optimize all migrated tables")
def optimize(all_tables):
    """Run OPTIMIZE TABLE FINAL on migrated tables."""
    if not all_tables:
        click.echo("Add --all to optimize all tables")
        return

    specs = load_tables()
    ch_client = get_ch_client()

    for spec in specs:
        status = get_status(ch_client, spec.pg_table)
        if status != "done":
            continue
        table_full = f"{spec.ch_database}.{spec.ch_table}"
        click.echo(f"OPTIMIZING {table_full} ...")
        ch_client.command(f"OPTIMIZE TABLE {table_full} FINAL")
        click.echo(f"  done")


@cli.command()
@click.option("--all", "all_tables", is_flag=True, help="Write sync_state for all migrated tables")
def write_sync_state(all_tables):
    """Write _meta.sync_state records for migrated tables."""
    if not all_tables:
        click.echo("Add --all to write sync_state for all tables")
        return

    specs = load_tables()
    ch_client = get_ch_client()
    total = 0

    for spec in specs:
        status = get_status(ch_client, spec.pg_table)
        if status != "done":
            continue
        count = write_sync_state_done(ch_client, spec)
        click.echo(f"{spec.pg_table}: {count} sync_state records written")
        total += count

    click.echo(f"\nTotal sync_state records: {total}")


def _migrate_one(spec: TableSpec, ch_client) -> None:
    """Migrate a single table."""
    status = get_status(ch_client, spec.pg_table)
    if status == "done":
        click.echo(f"SKIP {spec.pg_table} (already done)")
        return
    if status == "running":
        click.echo(f"RESET {spec.pg_table} (was running, resuming)")

    start = time.monotonic()
    started_at = datetime.now(timezone.utc)

    with pg_connection() as pg_conn:
        # Get column info
        pg_cols = get_pg_table_columns(pg_conn, spec.pg_table)
        ch_cols = _get_ch_columns(ch_client, spec.ch_database, spec.ch_table)

        # Resolve column alignment
        pg_in, ch_in = resolve_columns(
            pg_cols, ch_cols, spec.column_renames, spec.drop_pg_columns,
        )

        if not pg_in:
            click.echo(f"[ERROR] {spec.pg_table}: no matching columns between PG and CH")
            return

        # Get PG row count
        if spec.partitioned:
            pg_total = 0
            for year in spec.partition_years:
                partition = spec.partition_pattern.format(year=year)
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute(f"SELECT count(*) FROM {partition}")
                        pg_total += cur.fetchone()[0]
                except Exception:
                    pass
            if spec.include_default_partition:
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute(f"SELECT count(*) FROM {spec.pg_table}_default")
                        pg_total += cur.fetchone()[0]
                except Exception:
                    pass
        else:
            with pg_conn.cursor() as cur:
                cur.execute(f"SELECT count(*) FROM {spec.pg_table}")
                pg_total = cur.fetchone()[0]

        if pg_total == 0:
            click.echo(f"SKIP {spec.pg_table} (0 rows)")
            mark_done(ch_client, spec, 0)
            return

        mark_running(ch_client, spec, pg_total)
        click.echo(f"MIGRATING {spec.pg_table} ({pg_total:,} rows) ...")

        # Build order_by from columns that exist in PG table
        order_by = _build_order_by(pg_cols, spec.date_column)

        try:
            total_inserted = 0
            batch_count = 0

            if spec.partitioned:
                for partition_name, batches_iter in _partition_iterator(pg_conn, spec, pg_in):
                    for batch in batches_iter:
                        full_dicts = _rows_to_dicts(batch, pg_in)
                        write_batch(
                            ch_client, spec.ch_table, spec.ch_database,
                            pg_in, ch_in, batch, full_dicts,
                            table_name=spec.pg_table,
                        )
                        total_inserted += len(batch)
                        batch_count += 1
                        if batch_count % 10 == 0:
                            click.echo(f"  {batch_count} batches, {total_inserted:,} rows")
            else:
                for batch in iter_pg_rows(
                    pg_conn, spec.pg_table, pg_in,
                    batch_size=spec.batch_size,
                    order_by=order_by,
                ):
                    full_dicts = _rows_to_dicts(batch, pg_in)
                    write_batch(
                        ch_client, spec.ch_table, spec.ch_database,
                        pg_in, ch_in, batch, full_dicts,
                        table_name=spec.pg_table,
                    )
                    total_inserted += len(batch)
                    batch_count += 1
                    if batch_count % 10 == 0:
                        click.echo(f"  {batch_count} batches, {total_inserted:,} rows")

            elapsed = time.monotonic() - start
            mark_done(ch_client, spec, total_inserted)
            click.echo(
                f"[DONE] {spec.pg_table}: {total_inserted:,} rows in {elapsed:.1f}s "
                f"({total_inserted / max(elapsed, 0.001):,.0f} rows/sec)"
            )

        except Exception as e:
            mark_failed(ch_client, spec, str(e))
            click.echo(f"FAIL {spec.pg_table}: {e}")
            raise


def _build_order_by(pg_cols: list[str], date_col: str | None) -> str | None:
    """Build ORDER BY clause from columns that exist in the PG table."""
    candidates = ["ts_code", date_col, "code", "date", "ann_date"]
    parts = [c for c in candidates if c and c in pg_cols]
    return ", ".join(parts) if parts else None


def _partition_iterator(pg_conn, spec, columns):
    """Yield (partition_name, batch_iterator) for partitioned tables."""
    partition_tables = []
    for year in spec.partition_years:
        partition_tables.append(spec.partition_pattern.format(year=year))
    if spec.include_default_partition:
        partition_tables.append(f"{spec.pg_table}_default")

    for partition in partition_tables:
        with pg_conn.cursor() as cur:
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

        batches = iter_pg_rows(
            pg_conn, partition, columns,
            batch_size=spec.batch_size,
            order_by=f"ts_code, {spec.date_column}" if spec.date_column else "ts_code",
        )
        yield partition, batches


def _rows_to_dicts(batch: list[tuple], columns: list[str]) -> list[dict]:
    """Convert list of tuples to list of dicts."""
    return [dict(zip(columns, row)) for row in batch]


if __name__ == "__main__":
    cli()
