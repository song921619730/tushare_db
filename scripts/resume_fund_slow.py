"""Resume fund_sales_ratio and fund_sales_vol backfill with serial execution.

These two interfaces have a hard 5-calls-per-minute limit from Tushare.
Each interface is processed sequentially (one at a time), single-threaded,
with a 15-second delay between every API call.

Usage:
    python scripts/resume_fund_slow.py [--interface fund_sales_ratio] [--dry-run]
"""
import argparse
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv()

import clickhouse_connect

from tushare_db.config.loader import load_interface_specs
from tushare_db.core.concurrency_lock import ConcurrencyLock
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.core.tushare_client import TushareClient
from tushare_db.meta.sync_state import get_pending_units
from tushare_db.planner.planner import plan_units
from tushare_db.runner.worker import execute_unit


# Both slow interfaces
TARGET_INTERFACES = ["fund_sales_ratio", "fund_sales_vol"]

# 15-second delay between API calls (5 calls/min = 12s minimum, use 15s for safety)
CALL_DELAY_SEC = 15


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resume fund_sales_ratio/vol backfill (serial)")
    p.add_argument(
        "--interface",
        default=None,
        choices=TARGET_INTERFACES,
        help="Process only one interface",
    )
    p.add_argument("--dry-run", action="store_true", help="Plan units but do not execute")
    return p.parse_args()


def setup_logging() -> str:
    """Redirect stdout/stderr to log file. Returns log path."""
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/resume_fund_slow_{time.strftime('%Y%m%d_%H%M%S')}.log"
    sys.stdout = open(log_file, "w", encoding="utf-8")
    sys.stderr = sys.stdout
    return log_file


def _new_ch_client(database: str = "tushare") -> clickhouse_connect.driver.Client:
    """Create a ClickHouse client from environment configuration."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database=database,
    )


def run_serial(
    units,
    tushare_client: TushareClient,
    ch_client,
    run_id: uuid.UUID,
    delay_sec: float = CALL_DELAY_SEC,
) -> tuple[int, int, int]:
    """Execute units serially with delay between each call.

    Returns (total, done, failed).
    """
    total = len(units)
    done = 0
    failed = 0
    start_time = time.monotonic()

    print(f"  Serial execution: {total} units, ~{delay_sec}s between calls")
    eta_min = total * delay_sec / 60
    print(f"  Estimated time: ~{eta_min:.0f} minutes ({eta_min/60:.1f} hours)")

    for i, unit in enumerate(units):
        # Delay before each call (skip first)
        if i > 0:
            remaining = delay_sec
            while remaining > 0:
                sleep_for = min(remaining, 1.0)
                time.sleep(sleep_for)
                remaining -= sleep_for

        try:
            # Create a fresh CH client for this unit (like the worker does)
            unit_ch = _new_ch_client()
            rows = execute_unit(unit, tushare_client, unit_ch, run_id)
            unit_ch.close()

            if rows >= 0:
                done += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  ERROR unit {i+1}/{total}: {unit.scope_key} - {e}")

        # Progress log every 10 units
        if (i + 1) % 10 == 0 or i + 1 == total:
            elapsed = time.monotonic() - start_time
            pct = (i + 1) / total * 100
            rate = (i + 1) / elapsed * 60 if elapsed > 0 else 0
            remaining_units = total - i - 1
            eta_min = remaining_units / rate if rate > 0 else 0
            print(
                f"  Progress: {i+1}/{total} ({pct:.1f}%), "
                f"done={done}, failed={failed}, "
                f"rate={rate:.1f}/min, ETA={eta_min:.0f}min"
            )

    elapsed = time.monotonic() - start_time
    print(f"  Completed in {elapsed/60:.1f} minutes")
    return total, done, failed


def main() -> None:
    args = parse_args()
    log_file = setup_logging()

    print(f"Resume fund_slow starting... PID={os.getpid()}")
    print(f"Log file: {log_file}")

    # Acquire process-level lock
    lock = ConcurrencyLock()
    lock.acquire()

    # Connect to ClickHouse
    ch_client = _new_ch_client()

    # Create Tushare client — special RPM set to 4 (very conservative for 5/min limit)
    limiter = DualRateLimiter(normal_rpm=475, special_rpm=4)
    tushare_client = TushareClient(
        token=os.environ["TUSHARE_TOKEN"],
        limiter=limiter,
    )

    run_id = uuid.uuid4()
    grand_total = 0
    grand_done = 0
    grand_failed = 0

    try:
        # Load interface specs
        all_specs = load_interface_specs()
        interfaces = TARGET_INTERFACES if args.interface is None else [args.interface]

        for iface_name in interfaces:
            print(f"\n{'='*60}")
            print(f"Interface: {iface_name}")

            spec = next((s for s in all_specs if s.name == iface_name), None)
            if spec is None:
                print(f"  ERROR: interface {iface_name} not found in config")
                continue

            print(f"  Strategy:  {spec.fetch_strategy.kind}")
            print(f"  Bucket:    {spec.freq_bucket}")
            print(f"  Start:     {spec.start_date}")

            # Check existing pending units
            pending = get_pending_units(ch_client, spec.name)
            if pending:
                by_status = {}
                for u in pending:
                    st = u["status"]
                    by_status[st] = by_status.get(st, 0) + 1
                status_str = ", ".join(f"{k}:{v}" for k, v in sorted(by_status.items()))
                print(f"  Pending: {len(pending)} ({status_str})")
            else:
                print("  No pending units found (will plan fresh)")

            # Plan work units
            print("  Planning work units...")
            units = plan_units(spec, ch_client)
            print(f"  Planned {len(units)} work units")

            if args.dry_run:
                print("  DRY RUN: showing sample units")
                for u in units[:3]:
                    print(f"    {u.scope_key} params={u.params}")
                if len(units) > 3:
                    print(f"    ... and {len(units) - 3} more")
                continue

            # Filter to pending scope_keys if we have existing pending state
            if pending:
                pending_keys = {u["scope_key"] for u in pending}
                pending_units = [u for u in units if u.scope_key in pending_keys]
            else:
                pending_units = units

            if not pending_units:
                print("  No matching work units to execute")
                continue

            print(f"\n  Executing {len(pending_units)} units serially...")

            total, done, failed = run_serial(
                pending_units, tushare_client, ch_client, run_id,
            )
            grand_total += total
            grand_done += done
            grand_failed += failed
            print(f"  Result: {total} total, {done} done, {failed} failed")

        # Summary
        if not args.dry_run:
            print(f"\n{'='*60}")
            print(f"Grand total: {grand_total} units, {grand_done} done, {grand_failed} failed")

    finally:
        tushare_client.close()
        ch_client.close()
        lock.release()


if __name__ == "__main__":
    main()
