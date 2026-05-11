"""
Comprehensive retry v2: fix remaining failed + missing interfaces.

Fixes:
  - ccass_hold: shareholding Date→String (schema changed, config override added)
  - stk_nineturn: DateTime excluded from date name heuristic + date→datetime promotion
  - ths_hot: LowCardinality(String) None→"" filling

Skips: fund_sales_ratio, fund_sales_vol (5 RPM hard limit)
"""
import os, sys, uuid, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/retry_v2_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock

print(f"Comprehensive retry v2 starting... PID={os.getpid()}")
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

specs = load_interface_specs()
spec_map = {s.name: s for s in specs if s.enabled}
print(f"Enabled specs: {len(spec_map)}")

SKIP = {'fund_sales_ratio', 'fund_sales_vol', 'stk_weekly_monthly'}

# ── Step 1: Clean up ─────────────────────────────────────────────
print("\n=== Step 1: Clean up ===")

# Clean running entries (stuck from killed batch)
result = ch_client.query("""
    SELECT count() FROM _meta.sync_state
    WHERE status = 'running'
""")
running_cnt = result.result_rows[0][0]
if running_cnt > 0:
    print(f"Cleaning {running_cnt} stuck running entries...")
    ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE status = 'running'")
    time.sleep(2)
    print("  Done")

# ── Step 2: Identify work ───────────────────────────────────────
print("\n=== Step 2: Identify work ===")

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

# Interfaces not in sync_state at all
result = ch_client.query("SELECT DISTINCT interface FROM _meta.sync_state")
existing = {row[0] for row in result.result_rows}

# Include small missing + ccass_hold (cleaned in v2)
NEED_PLANNING = {'ccass_hold', 'fina_audit'}
missing_ifaces = [name for name in NEED_PLANNING if name not in existing and name not in SKIP]
if missing_ifaces:
    print(f"New interfaces (need full planning): {missing_ifaces}")
    for m in missing_ifaces:
        failed_by_iface[m] = set()

# Also add the 8 large missing (for full completeness - comment out if too much)
# LARGE_MISSING = {'cyq_chips', 'forecast', 'moneyflow_cnt_ths', 'moneyflow_ind_ths',
#                  'moneyflow_ths', 'pledge_detail', 'share_float', 'stk_holdernumber'}

# ── Step 3: Plan ────────────────────────────────────────────────
print("\n=== Step 3: Plan ===")

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
            filtered = [u for u in units if u.scope_key in target_keys]
            print(f"    {len(filtered)}/{len(units)} units to retry")
            all_units.extend(filtered)
        else:
            print(f"    {len(units)} new units")
            all_units.extend(units)
    except Exception as e:
        print(f"    ERROR: {e}")

print(f"\nTotal units: {len(all_units)}")

# Count buckets
normal = sum(1 for u in all_units if u.bucket == "normal")
special = sum(1 for u in all_units if u.bucket == "special")
print(f"  normal={normal}, special={special}")
est_min = len(all_units) / 400
print(f"  Est time: {est_min:.0f}min ({est_min/60:.1f}h)")

# ── Step 4: Execute ─────────────────────────────────────────────
if not all_units:
    print("No units to execute!")
    tushare_client.close()
    ch_client.close()
    sys.exit(0)

run_id = uuid.uuid4()
print(f"\n=== Step 4: Execute (run_id={run_id}) ===")
total, done, failed = execute_batch(all_units, tushare_client, ch_client, run_id=run_id)

elapsed = time.time() - start_ts
print(f"\n{'='*60}")
print(f"Complete! Total={total}, Done={done}, Failed={failed}")
print(f"Elapsed: {elapsed:.0f}s ({elapsed/60:.1f}min)")
print(f"{'='*60}")

# ── Final status ────────────────────────────────────────────────
print("\n=== Final Failed ===")
result = ch_client.query("""
    SELECT interface, count() as cnt, substring(max(last_error), 1, 200) as err
    FROM _meta.sync_state WHERE status = 'failed'
    GROUP BY interface ORDER BY interface
""")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]} — {row[2]}")

result = ch_client.query("SELECT status, count() FROM _meta.sync_state GROUP BY status ORDER BY status")
print("\nOverall:")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]}")

tushare_client.close()
ch_client.close()
print("Done!")
