"""Sequential backfill: 1 worker per interface, serial execution to avoid rate limits."""

from __future__ import annotations

import os
import sys
import time
import uuid

from dotenv import load_dotenv

load_dotenv()

from clickhouse_connect import get_client
from tushare_db.config.loader import load_interface_specs
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import plan_units
from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.executor import execute_batch
from tushare_db.meta.sync_state import get_pending_units


def main() -> None:
    interfaces = sys.argv[1:]
    if not interfaces:
        print("Usage: python serial_backfill.py <interface1> [interface2] ...")
        sys.exit(1)

    ch_client = get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=8123,
        username="pipeline",
        password=os.environ["CH_PIPELINE_PASSWORD"],
        database="tushare",
    )
    tushare = TushareClient(token=os.environ["TUSHARE_TOKEN"])

    all_specs = {s.name: s for s in load_interface_specs()}
    run_id = uuid.uuid4()
    total_done = 0
    total_failed = 0

    for name in interfaces:
        spec = all_specs.get(name)
        if not spec:
            print(f"  SKIP: {name} not found in specs")
            continue
        if not spec.enabled:
            print(f"  SKIP: {name} is disabled")
            continue

        # Plan units
        units = plan_units(spec, ch_client)
        if not units:
            print(f"  {name}: no units planned")
            continue

        # Filter to pending units only
        pending = get_pending_units(ch_client, spec.name)
        if pending:
            pending_keys = {u["scope_key"] for u in pending}
            pending_units = [u for u in units if u.scope_key in pending_keys]
        else:
            pending_units = units  # All units are pending (first run)

        if not pending_units:
            print(f"  {name}: all done ({len(units)} units)")
            continue

        print(f"  {name}: {len(pending_units)} units (total planned: {len(units)})")

        # Execute with 1 worker
        _, done_count, failed_count = execute_batch(
            pending_units, tushare, ch_client, run_id=run_id, max_workers=1,
        )
        total_done += done_count
        total_failed += failed_count
        print(f"  {name}: done={done_count}, failed={failed_count}")

        # Cool down between interfaces
        if len(interfaces) > 1:
            print("  Cooling down 60s...")
            time.sleep(60)

    print(f"\nTotal: done={total_done}, failed={total_failed}")
    tushare.close()
    ch_client.close()


if __name__ == "__main__":
    main()
