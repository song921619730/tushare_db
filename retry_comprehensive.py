"""
Comprehensive retry: plan failed/missing interfaces and execute.

Fixes applied in worker.py:
  - stk_nineturn: DateTime excluded from date name heuristic + date→datetime promotion
  - ths_hot: LowCardinality(String) None→"" filling
  - ccass_hold: Date type identified by column_types, not just name
  - Empty strings converted to None before default filling for all types

Skips: fund_sales_ratio, fund_sales_vol (5 RPM hard limit)
       stk_weekly_monthly (disabled interface)
"""
import os, sys, uuid, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/retry_comprehensive_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock

print(f"Comprehensive retry starting... PID={os.getpid()}")
start_ts = time.time()

lock = ConcurrencyLock()
lock.acquire()

ch_client = get_native_client(
    host=os.environ.get('CH_HOST', 'localhost'),
    port=8123,
    user='pipeline',
    password=os.environ.get('CH_PIPELINE_PASSWORD', '')
)

token = os.environ['TUSHARE_TOKEN']
limiter = DualRateLimiter(normal_rpm=475, special_rpm=285)
tushare_client = TushareClient(token=token, limiter=limiter)

# Load all specs
specs = load_interface_specs()
spec_map = {s.name: s for s in specs if s.enabled}
print(f"Enabled specs: {len(spec_map)}")

SKIP = {'fund_sales_ratio', 'fund_sales_vol', 'stk_weekly_monthly'}

# ── Step 1: Collect failed scope_keys and missing interfaces ──────
print("\n=== Step 1: Identify work to do ===")

# Get failed scope_keys (excluding skipped interfaces)
skip_clause = "', '".join(SKIP)
result = ch_client.query(f"""
    SELECT interface, scope_key FROM _meta.sync_state
    WHERE status = 'failed'
    AND interface NOT IN ('{skip_clause}')
    ORDER BY interface, scope_key
""")
failed_rows = [(row[0], row[1]) for row in result.result_rows]

failed_by_iface: dict[str, set[str]] = {}
for iface, sk in failed_rows:
    failed_by_iface.setdefault(iface, set()).add(sk)

print(f"Failed scope_keys: {len(failed_rows)} across {len(failed_by_iface)} interfaces")
for iface, keys in sorted(failed_by_iface.items()):
    print(f"  {iface}: {len(keys)} failed")

# Get running entries (stuck from old batch)
result = ch_client.query(f"""
    SELECT interface, scope_key FROM _meta.sync_state
    WHERE status = 'running'
    AND interface NOT IN ('{skip_clause}')
    ORDER BY interface, scope_key
""")
running_rows = [(row[0], row[1]) for row in result.result_rows]
for iface, sk in running_rows:
    failed_by_iface.setdefault(iface, set()).add(sk)

if running_rows:
    print(f"Running entries (will retry): {len(running_rows)}")
    for iface in set(r[0] for r in running_rows):
        count = sum(1 for r in running_rows if r[0] == iface)
        print(f"  {iface}: {count} running")

# Get interfaces not yet in sync_state at all
result = ch_client.query("SELECT DISTINCT interface FROM _meta.sync_state")
existing = {row[0] for row in result.result_rows}

# For now, only include missing interfaces that are small (period_loop)
# Larger missing (per_symbol, per_symbol_period, offset_paging) run separately
SMALL_MISSING = {'fina_audit'}  # period_loop, ~25 units
LARGE_MISSING = {'cyq_chips', 'forecast', 'moneyflow_cnt_ths', 'moneyflow_ind_ths',
                 'moneyflow_ths', 'pledge_detail', 'share_float', 'stk_holdernumber'}
missing_ifaces = [name for name in spec_map if name not in existing and name not in SKIP and name in SMALL_MISSING]
if missing_ifaces:
    print(f"Missing interfaces (need full planning): {len(missing_ifaces)}")
    for m in sorted(missing_ifaces):
        print(f"  {m}")
    # Add to failed_by_iface with empty set = plan ALL units
    for m in missing_ifaces:
        failed_by_iface[m] = set()

# Also clean up disabled interface stale entries
if 'stk_weekly_monthly' in existing:
    print("\nCleaning up stale stk_weekly_monthly entries...")
    ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE interface = 'stk_weekly_monthly'")
    time.sleep(1)
    print("  Done")

# ── Step 2: Plan and execute ──────────────────────────────────────
print("\n=== Step 2: Plan and execute ===")

all_units = []
for iface, target_keys in sorted(failed_by_iface.items()):
    if iface not in spec_map:
        print(f"  {iface}: not in specs, skipping")
        continue

    spec = spec_map[iface]
    print(f"  Planning {iface} (strategy={spec.fetch_strategy.kind})...")
    try:
        units = plan_units(spec, ch_client)
        if target_keys:
            # Only execute failed/running units
            filtered = [u for u in units if u.scope_key in target_keys]
            print(f"    {len(filtered)}/{len(units)} units to retry")
            all_units.extend(filtered)
        else:
            # New interface - execute all
            print(f"    {len(units)} new units")
            all_units.extend(units)
    except Exception as e:
        print(f"    ERROR planning: {e}")

print(f"\nTotal units to execute: {len(all_units)}")

if not all_units:
    print("No units to execute!")
    tushare_client.close()
    ch_client.close()
    sys.exit(0)

# Count by bucket
normal = sum(1 for u in all_units if u.bucket == "normal")
special = sum(1 for u in all_units if u.bucket == "special")
print(f"  normal={normal}, special={special}")

# Estimate time at ~400 units/min
est_min = len(all_units) / 400
print(f"  Estimated time: {est_min:.0f} min ({est_min/60:.1f}h)")

run_id = uuid.uuid4()
print(f"\nExecuting with run_id={run_id}...")
total, done, failed = execute_batch(all_units, tushare_client, ch_client, run_id=run_id)

elapsed = time.time() - start_ts
print(f"\n{'='*60}")
print(f"Comprehensive retry complete!")
print(f"Total: {total} units, Done: {done}, Failed: {failed}")
print(f"Elapsed: {elapsed:.0f}s ({elapsed/60:.1f}min)")
print(f"{'='*60}")

# ── Step 3: Final status report ───────────────────────────────────
print("\n=== Final Status ===")
result = ch_client.query("""
    SELECT interface, count() as cnt
    FROM _meta.sync_state
    WHERE status = 'failed'
    GROUP BY interface
    ORDER BY interface
""")
for row in result.result_rows:
    print(f"  FAILED {row[0]}: {row[1]}")

result = ch_client.query("""
    SELECT status, count() as cnt
    FROM _meta.sync_state
    GROUP BY status
    ORDER BY status
""")
print("\nOverall:")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]}")

tushare_client.close()
ch_client.close()
print("\nDone!")
