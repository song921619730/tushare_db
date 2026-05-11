"""
Final retry: dividend (rate limit failures), fina_audit (config fixed), dc_member.
Uses low concurrency to avoid per-interface rate limits.
"""
import os, sys, uuid, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

# Reduce worker count to avoid bursty rate limit
os.environ['TUSHARE_NORMAL_WORKERS'] = '4'
os.environ['TUSHARE_SPECIAL_WORKERS'] = '2'

os.makedirs('logs', exist_ok=True)
log_file = f"logs/retry_final_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock

print(f"Final retry starting... PID={os.getpid()}")
print(f"Workers: normal=4, special=2")
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

# ── Clean stuck running entries ──────────────────────────────
print("Clean stuck running entries...")
ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE status = 'running'")
time.sleep(1)

# ── Target interfaces ────────────────────────────────────────
TARGET = {'dividend', 'fina_audit', 'dc_member'}
SKIP = {'fund_sales_ratio', 'fund_sales_vol'}

# Get failed scope_keys
skip_clause = "', '".join(SKIP)
result = ch_client.query(f"""
    SELECT interface, scope_key FROM _meta.sync_state
    WHERE status = 'failed'
    AND interface IN ('dividend', 'fina_audit', 'dc_member')
    ORDER BY interface, scope_key
""")
failed_rows = [(row[0], row[1]) for row in result.result_rows]
failed_by_iface: dict[str, set[str]] = {}
for iface, sk in failed_rows:
    failed_by_iface.setdefault(iface, set()).add(sk)

print(f"\nFailed to retry:")
total_failed = 0
for iface, keys in sorted(failed_by_iface.items()):
    print(f"  {iface}: {len(keys)}")
    total_failed += len(keys)
print(f"  Total: {total_failed}")

# ── Plan and filter ──────────────────────────────────────────
all_units = []
for iface, target_keys in sorted(failed_by_iface.items()):
    if iface not in spec_map:
        print(f"  {iface}: not in specs, skipping")
        continue
    spec = spec_map[iface]
    print(f"  Planning {iface} (strategy={spec.fetch_strategy.kind})...")
    try:
        units = plan_units(spec, ch_client)
        filtered = [u for u in units if u.scope_key in target_keys]
        all_units.extend(filtered)
        print(f"    {len(filtered)}/{len(units)} units to retry")
    except Exception as e:
        print(f"    ERROR: {e}")

print(f"\nTotal units: {len(all_units)}")

normal = sum(1 for u in all_units if u.bucket == "normal")
special = sum(1 for u in all_units if u.bucket == "special")
print(f"  normal={normal}, special={special}")

if not all_units:
    print("No units to execute!")
    tushare_client.close()
    ch_client.close()
    sys.exit(0)

est_min = len(all_units) / 200  # slower due to fewer workers
print(f"  Est time: {est_min:.0f}min ({est_min/60:.1f}h)")

# ── Execute ──────────────────────────────────────────────────
run_id = uuid.uuid4()
print(f"\nExecuting (run_id={run_id})...")
total, done, failed = execute_batch(all_units, tushare_client, ch_client, run_id=run_id)

elapsed = time.time() - start_ts
print(f"\n{'='*60}")
print(f"Complete! Total={total}, Done={done}, Failed={failed}")
print(f"Elapsed: {elapsed:.0f}s ({elapsed/60:.1f}min)")

# ── Status ───────────────────────────────────────────────────
print("\n=== Failed ===")
result = ch_client.query("""
    SELECT interface, count(), substring(max(last_error), 1, 200)
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
