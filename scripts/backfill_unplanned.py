"""Backfill the 8 interfaces that have never been planned.

These interfaces exist in config but have no sync_state records.

Usage:
    python scripts/backfill_unplanned.py --interface cyq_chips
    python scripts/backfill_unplanned.py --all
    python scripts/backfill_unplanned.py --all --dry-run

Note: forecast (~137K units) is best run separately with --interface forecast.
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from clickhouse_connect import get_client

from tushare_db.config.loader import load_interface_specs
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.meta.sync_state import get_pending_units

# The 8 unplanned interfaces, ordered by estimated unit count (smallest first).
UNPLANNED = [
    "cyq_chips",
    "moneyflow_cnt_ths",
    "moneyflow_ind_ths",
    "moneyflow_ths",
    "pledge_detail",
    "share_float",
    "stk_holdernumber",
    "forecast",
]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Backfill 8 unplanned interfaces")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--interface",
        choices=UNPLANNED,
        help="Run a single interface",
    )
    group.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Run all 8 unplanned interfaces",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing",
    )
    args = parser.parse_args()

    dry_run = args.dry_run
    interfaces = UNPLANNED if args.run_all else [args.interface]

    ch_client = get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=8123,
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )
    tushare = TushareClient(token=os.environ["TUSHARE_TOKEN"])

    specs = {s.name: s for s in load_interface_specs()}
    total_units = 0
    total_done = 0
    total_failed = 0

    for name in interfaces:
        spec = specs.get(name)
        if not spec:
            print(f"  SKIP: {name} not found in specs")
            continue
        if not spec.enabled:
            print(f"  SKIP: {name} is disabled")
            continue

        units = plan_units(spec, ch_client)
        if not units:
            print(f"  {name}: no units planned")
            continue

        pending_keys = None
        existing = get_pending_units(ch_client, name)
        if existing:
            pending_keys = {u["scope_key"] for u in existing}

        if pending_keys is not None:
            pending_units = [u for u in units if u.scope_key in pending_keys]
        else:
            pending_units = units

        if not pending_units:
            print(f"  {name}: all done ({len(units)} units)")
            continue

        strategy = spec.fetch_strategy.kind
        print(
            f"  {name}: strategy={strategy}, planned={len(units)}, "
            f"pending={len(pending_units)}, bucket={spec.freq_bucket}"
        )

        if dry_run:
            if len(pending_units) <= 10:
                for u in pending_units:
                    print(f"    {u.scope_key}")
            else:
                for u in pending_units[:3]:
                    print(f"    {u.scope_key} (and {len(pending_units) - 6} more...)")
                print(f"    ... ({len(pending_units) - 6} units omitted)")
                for u in pending_units[-3:]:
                    print(f"    {u.scope_key}")
            total_units += len(pending_units)
            continue

        _, done_count, failed_count = execute_batch(
            pending_units, tushare, ch_client, max_workers=1,
        )
        total_units += len(pending_units)
        total_done += done_count
        total_failed += failed_count
        print(f"  {name}: done={done_count}, failed={failed_count}")

        if len(interfaces) > 1:
            print("  Cooling down 60s...")
            time.sleep(60)

    if dry_run:
        print(f"\nDry run: would backfill {total_units} units across {len(interfaces)} interface(s)")
    else:
        print(f"\nTotal: units={total_units}, done={total_done}, failed={total_failed}")

    tushare.close()
    ch_client.close()


if __name__ == "__main__":
    main()
