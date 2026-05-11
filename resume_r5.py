"""Resume round 5: retry cyq_perf (TOO_MANY_PARTS fixed), run index_weight (strategy fixed), retry remaining small failures."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_r5_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
import uuid

print(f"Resume R5: final retries + index_weight... PID={os.getpid()}")

ch_client = get_native_client(
    host=os.environ.get('CH_HOST', 'localhost'),
    port=8123,
    user='pipeline',
    password=os.environ.get('CH_PIPELINE_PASSWORD', '')
)
token = os.environ['TUSHARE_TOKEN']
limiter = DualRateLimiter(normal_rpm=475, special_rpm=285)
tushare_client = TushareClient(token=token, limiter=limiter)

now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
version = int(now.timestamp() * 1000)

specs = load_interface_specs()
enabled_specs = [s for s in specs if s.enabled]
run_id = uuid.uuid4()

# =============================================================================
# Step 1: Reset and retry cyq_perf failed units (TOO_MANY_PARTS was fixed)
# =============================================================================
print("\n=== Step 1: cyq_perf retry ===")
result = ch_client.query("SELECT count() FROM _meta.sync_state WHERE interface = 'cyq_perf' AND status = 'failed'")
cnt = result.result_rows[0][0]
print(f"  cyq_perf failed: {cnt}")
if cnt > 0:
    ch_client.command(f"""
        INSERT INTO _meta.sync_state
        SELECT interface, scope_key, 'pending', 0,
            toDateTime64('1970-01-01 00:00:00', 9, 'UTC'),
            toDateTime64('1970-01-01 00:00:00', 9, 'UTC'),
            attempts, '', {version}
        FROM _meta.sync_state
        WHERE interface = 'cyq_perf' AND status = 'failed'
    """)
    print(f"  Reset {cnt} failed units to pending")

cyq_spec = next((s for s in enabled_specs if s.name == 'cyq_perf'), None)
if cyq_spec:
    units = plan_units(cyq_spec, ch_client)
    pending_units = []
    for u in units:
        r = ch_client.query(f"""
            SELECT count() FROM _meta.sync_state
            WHERE interface = '{u.interface}' AND scope_key = '{u.scope_key}' AND status = 'done'
        """)
        if r.result_rows[0][0] == 0:
            pending_units.append(u)
    print(f"  {len(pending_units)} pending units (of {len(units)} total)")
    if pending_units:
        execute_batch(pending_units, tushare_client, ch_client, run_id=run_id)
        print(f"  Done")

# =============================================================================
# Step 2: Run index_weight with fixed date_loop config
# =============================================================================
print("\n=== Step 2: index_weight ===")
idx_spec = next((s for s in enabled_specs if s.name == 'index_weight'), None)
if idx_spec:
    print(f"  Strategy: {idx_spec.fetch_strategy.kind}")
    units = plan_units(idx_spec, ch_client)
    print(f"  {len(units)} total units")
    if units:
        execute_batch(units, tushare_client, ch_client, run_id=run_id)

# =============================================================================
# Step 3: Retry remaining small failures
# =============================================================================
print("\n=== Step 3: Retry small failures ===")
retry_names = {'fund_nav', 'stk_rewards', 'fund_company', 'stock_company', 'stk_managers', 'etf_index', 'index_basic', 'fund_factor_pro'}

for name in sorted(retry_names):
    result = ch_client.query(f"SELECT count() FROM _meta.sync_state WHERE interface = '{name}' AND status = 'failed'")
    cnt = result.result_rows[0][0]
    if cnt > 0:
        ch_client.command(f"""
            INSERT INTO _meta.sync_state
            SELECT interface, scope_key, 'pending', 0,
                toDateTime64('1970-01-01 00:00:00', 9, 'UTC'),
                toDateTime64('1970-01-01 00:00:00', 9, 'UTC'),
                attempts, '', {version}
            FROM _meta.sync_state
            WHERE interface = '{name}' AND status = 'failed'
        """)
        print(f"  {name}: reset {cnt} failed units")

retry_specs = [s for s in enabled_specs if s.name in retry_names]
for spec in retry_specs:
    units = plan_units(spec, ch_client)
    pending_units = []
    for u in units:
        r = ch_client.query(f"""
            SELECT count() FROM _meta.sync_state
            WHERE interface = '{u.interface}' AND scope_key = '{u.scope_key}' AND status = 'done'
        """)
        if r.result_rows[0][0] == 0:
            pending_units.append(u)

    if not pending_units:
        print(f"  {spec.name}: all done")
        continue

    print(f"  {spec.name}: {len(pending_units)} pending units")
    execute_batch(pending_units, tushare_client, ch_client, run_id=run_id)

# =============================================================================
# Final summary
# =============================================================================
print("\n=== Final Summary ===")
result = ch_client.query("SELECT status, count() FROM _meta.sync_state GROUP BY status")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]}")

result = ch_client.query("SELECT count(DISTINCT interface) FROM _meta.sync_state WHERE status = 'done'")
done_interfaces = result.result_rows[0][0]
print(f"\nInterfaces with done units: {done_interfaces}")

enabled_names = [s.name for s in enabled_specs]
result = ch_client.query("SELECT DISTINCT interface FROM _meta.sync_state WHERE status = 'done'")
synced_interfaces = {r[0] for r in result.result_rows}
not_done = [n for n in enabled_names if n not in synced_interfaces]
if not_done:
    print(f"Enabled interfaces with NO done units: {not_done}")

result = ch_client.query("""
    SELECT interface, count() as cnt FROM _meta.sync_state WHERE status = 'failed'
    GROUP BY interface ORDER BY cnt DESC LIMIT 10
""")
print("\nTop failed interfaces:")
for r in result.result_rows:
    print(f"  {r[0]}: {r[1]}")

tushare_client.close()
ch_client.close()
print("\nResume R5 complete.")
