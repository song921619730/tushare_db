"""
Retry dividend failures with low concurrency to avoid 500/min per-interface rate limit.

dc_member: API times out, cleaned from sync_state (to be disabled)
fina_audit: config changed to per_symbol_period, needs full re-plan (~137K units), deferred
"""
import os, sys, uuid, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

# Low concurrency to avoid bursty rate limits
os.environ['TUSHARE_NORMAL_WORKERS'] = '4'
os.environ['TUSHARE_SPECIAL_WORKERS'] = '2'

os.makedirs('logs', exist_ok=True)
log_file = f"logs/retry_dividend_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock

print(f"Dividend retry starting... PID={os.getpid()}")
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

# ── Clean ─────────────────────────────────────────────────────
print("Clean stuck running + useless entries...")
ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE status = 'running'")
time.sleep(1)
# Clean dc_member (API times out, not fixable)
ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE interface = 'dc_member'")
time.sleep(1)
# Clean fina_audit old entries (strategy changed, needs full re-plan)
ch_client.command("ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fina_audit'")
time.sleep(1)
print("Done.")

# ── Get failed dividend units ────────────────────────────────
result = ch_client.query("""
    SELECT scope_key FROM _meta.sync_state
    WHERE interface = 'dividend' AND status = 'failed'
    ORDER BY scope_key
""")
failed_keys = {row[0] for row in result.result_rows}
print(f"\nDividend failed units: {len(failed_keys)}")

if not failed_keys:
    print("No failed dividend units!")
    tushare_client.close()
    ch_client.close()
    sys.exit(0)

# ── Plan and filter ──────────────────────────────────────────
spec = spec_map['dividend']
print(f"Planning dividend (strategy={spec.fetch_strategy.kind})...")
units = plan_units(spec, ch_client)
filtered = [u for u in units if u.scope_key in failed_keys]
print(f"  {len(filtered)}/{len(units)} units to retry")

# ── Execute ──────────────────────────────────────────────────
run_id = uuid.uuid4()
print(f"\nExecuting {len(filtered)} units (run_id={run_id})...")
total, done, failed = execute_batch(filtered, tushare_client, ch_client, run_id=run_id)

elapsed = time.time() - start_ts
print(f"\n{'='*60}")
print(f"Complete! Total={total}, Done={done}, Failed={failed}")
print(f"Elapsed: {elapsed:.0f}s ({elapsed/60:.1f}min)")

# ── Final status ─────────────────────────────────────────────
result = ch_client.query("""
    SELECT interface, count(), substring(max(last_error), 1, 200)
    FROM _meta.sync_state WHERE status = 'failed'
    GROUP BY interface ORDER BY interface
""")
print("\n=== Remaining Failed ===")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]} — {row[2]}")

result = ch_client.query("SELECT status, count() FROM _meta.sync_state GROUP BY status ORDER BY status")
print("\nOverall:")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]}")

tushare_client.close()
ch_client.close()
print("Done!")
