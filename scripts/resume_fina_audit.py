"""Resume fina_audit backfill with reduced concurrency.

fina_audit uses per_symbol_period strategy (~5511 stocks x ~25 quarters = ~137K units).
Runs with 4 special workers to avoid overwhelming the Tushare API.

Usage:
    python scripts/resume_fina_audit.py [--dry-run] [--start 20200101] [--end 20260429]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Load .env manually (avoid dotenv dependency)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

import clickhouse_connect

from tushare_db.config.loader import load_interface_specs
from tushare_db.core.concurrency_lock import ConcurrencyLock
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.core.tushare_client import TushareClient
from tushare_db.meta.sync_state import get_pending_units
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resume fina_audit backfill")
    p.add_argument("--dry-run", action="store_true", help="Plan units but do not execute")
    p.add_argument("--start", default=None, help="Override start date (YYYYMMDD)")
    p.add_argument("--end", default=None, help="Override end date (YYYYMMDD)")
    return p.parse_args()


def setup_logging() -> str:
    """Redirect stdout/stderr to log file. Returns log path."""
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/resume_fina_audit_{time.strftime('%Y%m%d_%H%M%S')}.log"
    sys.stdout = open(log_file, "w", encoding="utf-8")
    sys.stderr = sys.stdout
    return log_file


INTERFACE_NAME = "fina_audit"


def main() -> None:
    args = parse_args()
    log_file = setup_logging()

    print(f"Resume fina_audit starting... PID={os.getpid()}")
    print(f"Log file: {log_file}")

    # Acquire process-level lock
    lock = ConcurrencyLock()
    lock.acquire()

    # Connect to ClickHouse
    ch_client = clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )

    # Create Tushare client with reduced special RPM to naturally throttle
    # 4 workers x ~1 call/15s = ~16 calls/min, so set special_rpm=15
    limiter = DualRateLimiter(normal_rpm=475, special_rpm=15)
    tushare_client = TushareClient(
        token=os.environ["TUSHARE_TOKEN"],
        limiter=limiter,
    )

    try:
        # Load fina_audit spec
        specs = load_interface_specs()
        spec = next((s for s in specs if s.name == INTERFACE_NAME), None)
        if spec is None:
            print(f"ERROR: interface {INTERFACE_NAME} not found in config")
            sys.exit(1)

        print(f"Interface: {spec.name}")
        print(f"Strategy:  {spec.fetch_strategy.kind}")
        print(f"Bucket:    {spec.freq_bucket}")
        print(f"Start:     {spec.start_date}")

        # Check existing pending units
        pending = get_pending_units(ch_client, spec.name)
        if pending:
            by_status = {}
            for u in pending:
                st = u["status"]
                by_status[st] = by_status.get(st, 0) + 1
            status_str = ", ".join(f"{k}:{v}" for k, v in sorted(by_status.items()))
            print(f"Pending units: {len(pending)} ({status_str})")
        else:
            print("No pending units found (will plan fresh)")

        # Plan work units
        print("Planning work units...")
        units = plan_units(spec, ch_client, start_date=args.start, end_date=args.end)
        print(f"Planned {len(units)} work units")

        if args.dry_run:
            print("DRY RUN: stopping before execution")
            # Show sample units
            for u in units[:5]:
                print(f"  {u.scope_key} params={u.params}")
            if len(units) > 5:
                print(f"  ... and {len(units) - 5} more")
            return

        # Filter to pending scope_keys if we have existing pending state
        if pending:
            pending_keys = {u["scope_key"] for u in pending}
            pending_units = [u for u in units if u.scope_key in pending_keys]
        else:
            # No existing state — run all units
            pending_units = units

        if not pending_units:
            print("No matching work units to execute")
            return

        print(f"Executing {len(pending_units)} units with 4 special workers...")

        # Override special workers to 4
        old_sw = os.environ.get("TUSHARE_SPECIAL_WORKERS")
        os.environ["TUSHARE_SPECIAL_WORKERS"] = "4"
        os.environ["TUSHARE_NORMAL_WORKERS"] = "0"  # no normal units for this interface

        try:
            _, done_count, failed_count = execute_batch(
                pending_units, tushare_client, ch_client,
            )
            print(f"\nResult: {len(pending_units)} total, {done_count} done, {failed_count} failed")
        finally:
            # Restore original env
            if old_sw is None:
                os.environ.pop("TUSHARE_SPECIAL_WORKERS", None)
            else:
                os.environ["TUSHARE_SPECIAL_WORKERS"] = old_sw

    finally:
        tushare_client.close()
        ch_client.close()
        lock.release()


if __name__ == "__main__":
    main()
