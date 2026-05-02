"""CLI entry point for tushare-db.

Commands:
  init          Create _meta tables and empty tushare database
  sample-apis   Sample API responses for schema inference
  probe         Detect interface permissions
  rebuild-schema Rebuild ClickHouse schema from sampled data
  bootstrap     Full cold-start: sample → infer → CREATE → seed → probe
  backfill      Historical data backfill (PR3)
  status        Show sync status (PR3)
  resume        Resume failed/partial units (PR3)
  update        Incremental update (PR4)
  verify        Data verification (PR6)
  scheduler-run Start APScheduler daemon (PR4)
  mcp-serve     Start MCP server (PR5)
"""

from __future__ import annotations

import os
import sys
import time

import click
from dotenv import load_dotenv

from tushare_db.core.concurrency_lock import ConcurrencyLock
from tushare_db.logging_setup import setup_logging
from tushare_db.meta.bootstrap import (
    get_client,
    init_meta,
    init_tushare_db,
    verify_init,
)
from tushare_db.sink.clickhouse_sink import get_native_client

load_dotenv()


def _get_ch_native():
    """Get ClickHouse Native protocol client for data operations."""
    host = os.environ.get("CH_HOST", "localhost")
    password = os.environ.get("CH_PIPELINE_PASSWORD", "")
    return get_native_client(host=host, port=8123, user="pipeline", password=password)


def _get_tushare_client():
    """Get Tushare API client."""
    from tushare_db.core.tushare_client import TushareClient
    from tushare_db.core.rate_limiter import DualRateLimiter

    token = os.environ["TUSHARE_TOKEN"]
    if token == "PASTE_YOUR_NEW_TUSHARE_TOKEN_HERE":
        raise ValueError("TUSHARE_TOKEN not set in .env")

    limiter = DualRateLimiter(normal_rpm=475, special_rpm=285)
    return TushareClient(token=token, limiter=limiter)


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.pass_context
def cli(ctx: click.Context, log_level: str) -> None:
    """Tushare Pro A-share data warehouse CLI."""
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    setup_logging(level=log_level)


@cli.command()
@click.option("--host", default=os.environ.get("CH_HOST", "localhost"))
@click.option("--port", default=int(os.environ.get("CH_HTTP_PORT", "8123")))
@click.option("--user", default=os.environ.get("CH_USER", "pipeline"))
@click.option("--password", default=os.environ.get("CH_PIPELINE_PASSWORD", ""))
def init(host: str, port: int, user: str, password: str) -> None:
    """Initialize ClickHouse: create _meta tables + empty tushare database."""
    click.echo("Initializing tushare-db...")

    client = get_client(host=host, http_port=port, user=user, password=password)

    try:
        init_meta(client)
        init_tushare_db(client)
        verify_init(client)
        click.echo("OK: _meta tables and tushare database created successfully.")
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.option("--only", default=None, help="Comma-separated interface names to sample")
@click.option("--output-dir", default="data/samples")
def sample_apis(only: str | None, output_dir: str) -> None:
    """Sample Tushare API responses for schema inference."""
    import json
    from pathlib import Path
    from tushare_db.config.loader import load_interface_specs

    setup_logging()
    token = os.environ.get("TUSHARE_TOKEN", "")
    if token == "PASTE_YOUR_NEW_TUSHARE_TOKEN_HERE":
        click.echo("ERROR: TUSHARE_TOKEN not set in .env", err=True)
        sys.exit(1)

    specs = load_interface_specs()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if only:
        target_names = {n.strip() for n in only.split(",")}
        specs = [s for s in specs if s.name in target_names]
    else:
        specs = [s for s in specs if s.enabled]

    click.echo(f"Sampling {len(specs)} interfaces...")

    with _get_tushare_client() as client:
        for spec in specs:
            try:
                response = _sample_one_interface(client, spec)
                if response is None:
                    continue
                output_file = output_path / f"{spec.name}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(response, f, indent=2, ensure_ascii=False)
                fields = response.get("data", {}).get("fields", [])
                items = response.get("data", {}).get("items", [])
                click.echo(f"  {spec.name}: {len(fields)} fields, {len(items)} rows")
                time.sleep(0.2)
            except Exception as e:
                click.echo(f"  {spec.name}: FAILED ({e})")

    click.echo(f"OK: Samples saved to {output_dir}/")


def _sample_one_interface(client, spec) -> dict | None:
    """Make a minimal API call for sampling."""
    strategy = spec.fetch_strategy.kind
    params: dict = {}
    if strategy in ("date_loop", "offset_paging"):
        params = {"trade_date": "20240102"}  # first trading day of 2024 (Jan 1 is holiday)
    elif strategy == "period_loop":
        params = {"period": "20240331"}
    elif strategy == "per_symbol_period":
        params = {"ts_code": "000001.SZ", "period": "20240331"}
    elif strategy == "monthly_window":
        params = {"month": "202401"}
    return client.call(spec.name, bucket=spec.freq_bucket, **params)


def _seed_trade_cal_internal(ch_client) -> int:
    """Fetch and seed the trade_cal table."""
    from datetime import datetime
    from tushare_db.sink.clickhouse_sink import insert_rows

    # Create table if not exists
    ch_client.command(
        "CREATE TABLE IF NOT EXISTS _meta.trade_cal ("
        "    exchange  LowCardinality(String),"
        "    cal_date  Date,"
        "    is_open   UInt8,"
        "    pretrade_date Nullable(Date),"
        "    _version  UInt64"
        ") ENGINE = ReplacingMergeTree(_version) "
        "PARTITION BY tuple() "
        "ORDER BY (exchange, cal_date)"
    )

    response = _get_tushare_client().call("trade_cal", bucket="normal", exchange="SSE")
    fields = response.get("data", {}).get("fields", [])
    items = response.get("data", {}).get("items", [])

    if not items:
        click.echo("  trade_cal: no data received from Tushare")
        return 0

    # Normalize dates YYYYMMDD -> datetime.date objects; None stays None
    date_indices = [i for i, f in enumerate(fields) if "date" in f.lower()]
    for item in items:
        for idx in date_indices:
            if idx < len(item) and item[idx] and isinstance(item[idx], str):
                val = item[idx].strip()
                if len(val) == 8 and val.isdigit():
                    item[idx] = datetime.strptime(val, "%Y%m%d").date()

    # Drop rows where date columns are None (clickhouse_connect can't serialize None into Date)
    items = [item for item in items if all(item[i] is not None for i in date_indices)]

    insert_rows(ch_client, table="trade_cal", columns=fields, rows=items, database="_meta")
    click.echo(f"  trade_cal: {len(items)} rows seeded")
    return len(items)


@cli.command()
def probe() -> None:
    """Probe each interface for permissions, write back YAML enabled flag."""
    from pathlib import Path

    from ruamel.yaml import YAML

    from tushare_db.config.loader import load_all_interface_specs

    token = os.environ.get("TUSHARE_TOKEN", "")
    if token == "PASTE_YOUR_NEW_TUSHARE_TOKEN_HERE":
        click.echo("ERROR: TUSHARE_TOKEN not set in .env", err=True)
        sys.exit(1)

    specs = load_all_interface_specs()
    enabled_count = 0
    disabled_count = 0
    # Track changes: interface_name -> new_enabled value
    changes: dict[str, bool] = {}

    with _get_tushare_client() as client:
        for spec in specs:
            try:
                if spec.fetch_strategy.kind == "date_loop":
                    client.call(spec.name, bucket=spec.freq_bucket, trade_date="20240101")
                elif spec.fetch_strategy.kind == "period_loop":
                    client.call(spec.name, bucket=spec.freq_bucket, period="20240331")
                elif spec.fetch_strategy.kind == "full_once":
                    client.call(spec.name, bucket=spec.freq_bucket)
                else:
                    client.call(spec.name, bucket=spec.freq_bucket)

                if not spec.enabled:
                    click.echo(f"  {spec.name}: DISABLED -> ENABLED (was paid, now accessible)")
                    changes[spec.name] = True

                enabled_count += 1
                time.sleep(0.15)
            except Exception as e:
                if spec.enabled:
                    click.echo(f"  {spec.name}: ENABLED -> DISABLED ({e})")
                    changes[spec.name] = False
                    disabled_count += 1
                else:
                    click.echo(f"  {spec.name}: DISABLED (expected, {type(e).__name__})")

    # Write back YAML changes
    if changes:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        # Group changes by source file
        file_changes: dict[str, list[tuple[str, bool]]] = {}
        for spec in specs:
            if spec.name in changes:
                src = getattr(spec, "__source_file__", None)
                if src:
                    file_changes.setdefault(src, []).append((spec.name, changes[spec.name]))

        for yaml_file, iface_changes in file_changes.items():
            _write_yaml_enabled(yaml, yaml_file, iface_changes)

    click.echo(f"Probe complete: {enabled_count} accessible, {disabled_count} newly disabled")
    if changes:
        click.echo(f"OK: {len(changes)} YAML file(s) updated with enabled/disabled status")


def _write_yaml_enabled(
    yaml: YAML,
    yaml_file: str,
    changes: list[tuple[str, bool]],
) -> None:
    """Update `enabled` field for specific interfaces in a multi-document YAML file."""
    changed_names = {name for name, _ in changes}
    enabled_map = {name: val for name, val in changes}

    path = Path(yaml_file)
    documents = list(yaml.load_all(path))

    for doc in documents:
        if doc and "name" in doc and doc["name"] in changed_names:
            doc["enabled"] = enabled_map[doc["name"]]

    with open(path, "w", encoding="utf-8") as f:
        for i, doc in enumerate(documents):
            if i > 0:
                f.write("---\n")
            yaml.dump(doc, f)


@cli.command()
@click.option("--interface", default=None, help="Rebuild schema for specific interface")
@click.option("--sample-dir", default="data/samples")
@click.option("--ch-host", default=os.environ.get("CH_HOST", "localhost"))
@click.option("--ch-password", default=os.environ.get("CH_PIPELINE_PASSWORD", ""))
def rebuild_schema(interface: str | None, sample_dir: str, ch_host: str, ch_password: str) -> None:
    """Rebuild ClickHouse schema from sampled data."""
    import json
    from pathlib import Path
    from tushare_db.config.loader import load_interface_specs
    from tushare_db.schema.inferer import infer_schema
    from tushare_db.schema.ddl_builder import build_create_table

    specs = load_interface_specs()
    if only := interface:
        target_names = {n.strip() for n in only.split(",")}
        specs = [s for s in specs if s.name in target_names]
    else:
        specs = [s for s in specs if s.enabled]

    sample_path = Path(sample_dir)
    ch_client = get_native_client(host=ch_host, port=8123, user="pipeline", password=ch_password)
    tables_created = 0

    try:
        for spec in specs:
            sample_file = sample_path / f"{spec.name}.json"
            if not sample_file.exists():
                click.echo(f"  {spec.name}: SKIP (no sample)")
                continue

            columns = infer_schema(
                sample_file,
                field_names=spec.fields or None,
                overrides=spec.schema_overrides or None,
            )

            table_name = f"tushare.{spec.table}"
            ddl = build_create_table(
                table_name=table_name,
                columns=columns,
                partition_key=spec.partition_key or "tuple()",
                order_by=spec.order_by or "ts_code, trade_date",
            )

            ch_client.command(ddl)
            click.echo(f"  {spec.name}: {table_name} ({len(columns)} columns)")
            tables_created += 1

        click.echo(f"OK: {tables_created} table(s) created/rebuilt")
    finally:
        ch_client.close()


@cli.command()
@click.option("--only", default=None, help="Comma-separated interface names to process")
@click.option("--ch-host", default=os.environ.get("CH_HOST", "localhost"))
@click.option("--ch-password", default=os.environ.get("CH_PIPELINE_PASSWORD", ""))
def bootstrap(only: str | None, ch_host: str, ch_password: str) -> None:
    """Full cold-start: sample → infer → CREATE tables → seed trade_cal.

    Sequence:
    1. Sample all enabled interfaces from Tushare
    2. Infer ClickHouse schemas and CREATE tables
    3. Seed trade_cal (trading calendar)
    """
    import json
    from pathlib import Path
    from tushare_db.config.loader import load_interface_specs
    from tushare_db.schema.inferer import infer_schema
    from tushare_db.schema.ddl_builder import build_create_table

    click.echo("Bootstrap starting...")

    # Load specs
    specs = load_interface_specs()
    if only:
        target_names = {n.strip() for n in only.split(",")}
        specs = [s for s in specs if s.name in target_names]
    else:
        specs = [s for s in specs if s.enabled]

    sample_path = Path("data/samples")
    sample_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Sample APIs
    click.echo(f"Step 1/3: Sampling {len(specs)} APIs...")
    with _get_tushare_client() as tushare_client:
        for spec in specs:
            try:
                response = _sample_one_interface(tushare_client, spec)
                if response is None:
                    continue
                sample_file = sample_path / f"{spec.name}.json"
                with open(sample_file, "w", encoding="utf-8") as f:
                    json.dump(response, f, indent=2, ensure_ascii=False)
                fields = response.get("data", {}).get("fields", [])
                items = response.get("data", {}).get("items", [])
                click.echo(f"  {spec.name}: {len(fields)} fields, {len(items)} rows")
                time.sleep(0.2)
            except Exception as e:
                click.echo(f"  {spec.name}: SKIP ({type(e).__name__})")

    # Step 2: Create tables from samples
    click.echo("Step 2/3: Creating ClickHouse tables...")
    ch_client = get_native_client(host=ch_host, port=8123, user="pipeline", password=ch_password)
    tables_created = 0

    try:
        for spec in specs:
            sample_file = sample_path / f"{spec.name}.json"
            if not sample_file.exists():
                click.echo(f"  {spec.name}: SKIP (no sample)")
                continue

            columns = infer_schema(
                sample_file,
                field_names=spec.fields or None,
                overrides=spec.schema_overrides or None,
            )

            # Validate partition_key and order_by columns exist in schema
            col_names = {c[0] for c in columns}
            partition_key = spec.partition_key or "tuple()"
            order_by = spec.order_by or "ts_code, trade_date"

            def _cols_in_schema(expr: str) -> bool:
                """Check all column references in a simple expression exist."""
                import re
                refs = re.findall(r'[a-z_]+', expr.lower())
                return all(r in col_names or r in ('totuple', 'tuple', 'toyyyymm', 'toint16', 'intdiv', 'div', 'yyyymm', 'cast') for r in refs)

            if not _cols_in_schema(partition_key):
                click.echo(f"  {spec.name}: WARNING: partition_key {partition_key} uses columns not in schema, falling back to tuple()")
                partition_key = "tuple()"

            # Extract order_by column names (strip functions)
            import re
            order_cols = [c.strip() for c in re.split(r'[,()]', order_by) if c.strip() and c.strip() != 'tuple()']
            missing_order = [c for c in order_cols if c not in col_names]
            if missing_order:
                # Add missing ORDER BY columns as String (non-nullable, required for sorting key)
                for col in missing_order:
                    columns.append((col, "String"))
                    col_names.add(col)
                click.echo(f"  {spec.name}: Added missing order_by columns {missing_order}")

            table_name = f"tushare.{spec.table}"
            ddl = build_create_table(
                table_name=table_name,
                columns=columns,
                partition_key=partition_key,
                order_by=order_by,
            )

            try:
                ch_client.command(ddl)
                click.echo(f"  {spec.name}: {table_name} ({len(columns)} columns)")
                tables_created += 1
            except Exception as e:
                click.echo(f"  {spec.name}: ERROR creating table ({e})", err=True)

        # Step 3: Seed trade_cal
        click.echo("Step 3/3: Seeding trade_cal...")
        _seed_trade_cal_internal(ch_client)

        click.echo(f"\nBootstrap complete: {tables_created} tables created")
    finally:
        ch_client.close()


# ---------------------------------------------------------------------------
# PR3+ commands (stubs)
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--layer", type=int, default=None, help="Backfill layer 0-5")
@click.option("--priority", default=None, help="P0|P1|P2|P3")
@click.option("--interface", default=None, help="Specific interface name")
@click.option("--from", "from_date", default=None, help="Start date YYYYMMDD")
@click.option("--to", "to_date", default=None, help="End date YYYYMMDD")
@click.option("--all", "backfill_all", is_flag=True, help="Backfill everything")
def backfill(
    layer: int | None,
    priority: str | None,
    interface: str | None,
    from_date: str | None,
    to_date: str | None,
    backfill_all: bool,
) -> None:
    """Backfill historical data for specified interfaces."""
    from tushare_db.runner.backfill import select_specs, run_backfill
    from tushare_db.runner.verify_hook import make_verify_hook

    lock = ConcurrencyLock()
    lock.acquire()

    specs = select_specs(layer=layer, priority=priority, interface=interface, backfill_all=backfill_all)
    if not specs:
        click.echo("No matching interfaces found.")
        return

    ch_client = _get_ch_native()
    tushare_client = _get_tushare_client()

    verify_hook = make_verify_hook()

    try:
        summary = run_backfill(specs, tushare_client, ch_client, start_date=from_date, end_date=to_date, verify_hook=verify_hook)
        click.echo(
            f"Backfill complete: {summary['done']}/{summary['total']} done, "
            f"{summary['failed']} failed"
        )
    finally:
        tushare_client.close()
        ch_client.close()


def _get_layer(spec) -> int:
    """Map an InterfaceSpec to its backfill layer (0-5). Kept for CLI status command."""
    from tushare_db.runner.backfill import get_layer
    return get_layer(spec)


@cli.command()
@click.option("--interface", default=None, help="Specific interface")
@click.option("--detail", is_flag=True, help="Show detailed status")
def status(interface: str | None, detail: bool) -> None:
    """[PR3] Show sync status from _meta.sync_state."""
    from tushare_db.meta.sync_state import get_interface_status, get_pending_units

    ch_client = _get_ch_native()
    try:
        if interface:
            rows = get_interface_status(ch_client, interface)
            if not rows:
                click.echo(f"No sync state found for {interface}")
                return

            click.echo(f"Status for {interface}:")
            if detail:
                for row in rows:
                    error = f" — {row['last_error']}" if row.get('last_error') else ""
                    click.echo(
                        f"  {row['scope_key']}: {row['status']} "
                        f"({row['rows']} rows, {row['attempts']} retries)"
                        f"{error}"
                    )
            else:
                # Summary by status
                status_counts: dict[str, int] = {}
                total_rows = 0
                for row in rows:
                    s = row["status"]
                    status_counts[s] = status_counts.get(s, 0) + 1
                    total_rows += row.get("rows", 0)
                for s, c in sorted(status_counts.items()):
                    click.echo(f"  {s}: {c} units")
                click.echo(f"  total rows: {total_rows}")
        else:
            # Show summary across all interfaces
            result = ch_client.query(
                "SELECT interface, status, count() as cnt FROM _meta.sync_state FINAL "
                "GROUP BY interface, status ORDER BY interface, status"
            )
            if not result.result_rows:
                click.echo("No sync state found. Run backfill first.")
                return

            current_interface = None
            status_totals: dict[str, int] = {}
            for row in result.result_rows:
                iface, st, cnt = row[0], row[1], row[2]
                status_totals[st] = status_totals.get(st, 0) + cnt
                if detail:
                    if iface != current_interface:
                        click.echo(f"\n{iface}:")
                        current_interface = iface
                    click.echo(f"  {st}: {cnt} units")

            if not detail:
                click.echo("Overall sync status:")
                for st, cnt in sorted(status_totals.items()):
                    click.echo(f"  {st}: {cnt} units")
                click.echo(f"  total: {sum(status_totals.values())} units")
    finally:
        ch_client.close()


@cli.command()
@click.option("--interface", default=None, help="Only resume specific interface")
@click.option("--dry-run", is_flag=True, help="Show what would be resumed without executing")
def resume(interface: str | None, dry_run: bool) -> None:
    """[PR3] Resume all failed/partial sync units."""
    import uuid
    from tushare_db.config.loader import load_interface_specs
    from tushare_db.planner.planner import plan_units
    from tushare_db.runner.executor import execute_batch
    from tushare_db.meta.sync_state import get_pending_units

    lock = ConcurrencyLock()
    lock.acquire()

    specs = load_interface_specs()
    if interface:
        specs = [s for s in specs if s.name == interface]
    else:
        specs = [s for s in specs if s.enabled]

    ch_client = _get_ch_native()
    tushare_client = _get_tushare_client()

    run_id = uuid.uuid4()
    total_units = 0
    total_done = 0
    total_failed = 0

    try:
        for spec in specs:
            pending = get_pending_units(ch_client, spec.name)
            if not pending:
                continue

            click.echo(f"  {spec.name}: {len(pending)} pending units ({_pending_summary(pending)})")

            if dry_run:
                total_units += len(pending)
                continue

            # Re-plan units for this interface (includes date range from spec)
            units = plan_units(spec, ch_client)
            if not units:
                continue

            # Filter to only pending scope_keys
            pending_keys = {u["scope_key"] for u in pending}
            pending_units = [u for u in units if u.scope_key in pending_keys]

            if len(pending_units) < len(pending):
                missing = len(pending) - len(pending_units)
                click.echo(f"    {spec.name}: warning: {missing} pending scope_keys have no matching planned unit")

            if not pending_units:
                click.echo(f"    {spec.name}: no matching work units to resume")
                continue

            total_units += len(pending_units)
            click.echo(f"    {spec.name}: resuming {len(pending_units)} units")

            done, done_count, failed_count = execute_batch(
                pending_units, tushare_client, ch_client, run_id=run_id,
            )
            total_done += done_count
            total_failed += failed_count

        if dry_run:
            click.echo(f"\nResume dry-run: {total_units} units would be retried")
        else:
            click.echo(f"\nResume complete: {total_units} units, {total_done} done, {total_failed} failed")
    finally:
        tushare_client.close()
        ch_client.close()


def _pending_summary(pending: list[dict]) -> str:
    """Summarize pending units by status."""
    counts: dict[str, int] = {}
    for u in pending:
        s = u["status"]
        counts[s] = counts.get(s, 0) + 1
    return ", ".join(f"{s}: {c}" for s, c in sorted(counts.items()))


@cli.command()
@click.option("--batch", default=None, help="A|B|C|D|saturday|reference")
@click.option("--incremental", is_flag=True, help="Incremental update for all enabled interfaces")
def update(batch: str | None, incremental: bool) -> None:
    """[PR4] Incremental update (T-1)."""
    from tushare_db.runner.incremental import run_incremental

    lock = ConcurrencyLock()
    lock.acquire()

    ch_client = _get_ch_native()
    tushare_client = _get_tushare_client()

    try:
        result = run_incremental(ch_client, tushare_client, batch=batch)
        if result.get("skipped"):
            click.echo(f"Skipped: {result.get('reason', 'unknown')}")
            return

        click.echo(
            f"Update complete: {result['done']}/{result['total']} units, "
            f"{result['failed']} failed (target: {result['target_date']})"
        )
    finally:
        tushare_client.close()
        ch_client.close()


@cli.command()
@click.option("--priority", default=None, help="P0|P1|P2|P3")
@click.option("--interface", default=None, help="Specific interface name")
@click.option("--gaps", is_flag=True, help="Also run gap detection")
@click.option("--checksums", is_flag=True, help="Also compute checksums")
def verify(priority: str | None, interface: str | None, gaps: bool, checksums: bool) -> None:
    """[PR6] Data verification (row counts, gap detection, checksums)."""
    ch_client = _get_ch_native()

    try:
        # Row counts
        from tushare_db.verify.row_counts import verify_row_counts

        click.echo("=== Row Count Verification ===")
        row_results = verify_row_counts(ch_client, priority=priority, interface=interface)
        ok_count = sum(1 for r in row_results if r["status"] == "ok")
        issue_count = sum(1 for r in row_results if r["status"] != "ok")

        for r in row_results:
            if r["status"] != "ok":
                click.echo(f"  [{r['status']}] {r['interface']}: {r.get('issue', r.get('table', ''))}")

        click.echo(f"  OK: {ok_count}, Issues: {issue_count}")

        # Gap detection
        if gaps:
            click.echo("\n=== Gap Detection ===")
            from tushare_db.verify.gap_detector import detect_gaps

            gap_results = detect_gaps(ch_client, interface=interface)
            if not gap_results:
                click.echo("  No gaps detected")
            else:
                for g in gap_results:
                    gap_type = g.get("gap_type", "unknown")
                    dates_key = "missing_dates" if gap_type == "trading_day" else "missing_periods"
                    dates = g.get(dates_key, [])
                    click.echo(
                        f"  [{g['interface']}] ({gap_type}) {g['missing_count']} missing "
                        f"({g['date_range']}): {dates[:5]}{'...' if len(dates) > 5 else ''}"
                    )

        # Checksums
        if checksums:
            click.echo("\n=== Data Checksums ===")
            from tushare_db.verify.checksums import compute_checksums

            cs_results = compute_checksums(ch_client, interface=interface, priority=priority)
            for cs in cs_results:
                if cs.get("error"):
                    click.echo(f"  [ERROR] {cs['interface']}: {cs['error']}")
                else:
                    click.echo(
                        f"  {cs['interface']}: {cs['row_count']} rows, "
                        f"fp={cs['fingerprint']}"
                    )
    finally:
        ch_client.close()


@cli.command(name="reset-state")
@click.option("--interface", required=True, help="Interface name to reset")
@click.option("--confirm", is_flag=True, help="Actually delete (without this is dry-run)")
def reset_state(interface: str, confirm: bool) -> None:
    """Delete all sync_state rows for an interface (use after strategy change)."""
    ch = _get_ch_native()
    try:
        result = ch.query(
            f"SELECT count(), countIf(status='done'), countIf(status='failed'), countIf(status='running') "
            f"FROM _meta.sync_state WHERE interface = '{interface}'"
        )
        row = result.result_rows[0] if result.result_rows else (0, 0, 0, 0)
        print(f"Found {row[0]} rows for {interface} (done={row[1]}, failed={row[2]}, running={row[3]})")
        if not confirm:
            print("Dry-run; pass --confirm to actually delete")
            return
        ch.command(f"ALTER TABLE _meta.sync_state DELETE WHERE interface = '{interface}'")
        print(f"Deleted. Re-plan with: tushare-db backfill --interface {interface}")
    finally:
        ch.close()


@cli.command()
def scheduler_run() -> None:
    """[PR4] Start the APScheduler daemon (container entrypoint)."""
    from tushare_db.scheduler.service import start_scheduler

    click.echo("Starting scheduler...")
    start_scheduler()


@cli.command()
@click.option("--transport", default="stdio", type=click.Choice(["stdio", "sse"]))
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=7800)
def mcp_serve(transport: str, host: str, port: int) -> None:
    """[PR5] Start MCP server (stdio or SSE transport)."""
    from tushare_db.mcp_server.server import run_stdio, run_sse

    if transport == "stdio":
        click.echo("Starting MCP server (stdio)...")
        run_stdio()
    else:
        click.echo(f"Starting MCP server (SSE) on {host}:{port}...")
        run_sse(host=host, port=port)


def main() -> None:
    """Entry point defined in pyproject.toml [project.scripts]."""
    cli()


if __name__ == "__main__":
    main()
