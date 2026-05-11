"""Resume round 4: clean up stale sync_state and re-run fixed interfaces.

Changes applied in this round:
- Changed from date_loop to full_once: cn_gdp, shibor, shibor_lpr, shibor_quote,
  us_tbr, us_tltr, us_trltr, us_trycr, us_tycr, sf_month, gz_index, wz_index,
  fut_weekly_detail
- Changed from date_loop to per_symbol: cyq_perf
- Clean up stale pending/failed units from R3: cn_cpi, cn_m, cn_ppi, hibor, libor
- Also retry remaining small-failure interfaces: fund_nav, fund_factor_pro, stk_rewards, etc.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_r4_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock
import uuid

print(f"Resume R4: cleanup + re-run starting... PID={os.getpid()}")

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

# =============================================================================
# Step 1: Clean up stale sync_state entries for strategy-changed interfaces
# =============================================================================
print("\n=== Step 1: Cleaning stale sync_state entries ===")

# Interfaces that changed from date_loop to full_once (R3 + R4)
full_once_interfaces = [
    'cn_cpi', 'cn_m', 'cn_ppi', 'hibor', 'libor',  # R3 fixes
    'cn_gdp', 'shibor', 'shibor_lpr', 'shibor_quote',  # R4 macro fixes
    'us_tbr', 'us_tltr', 'us_trltr', 'us_trycr', 'us_tycr',  # R4 macro fixes
    'sf_month', 'gz_index', 'wz_index',  # R4 macro fixes
    'fut_weekly_detail',  # R4 futures fix
]

# Interfaces that changed from date_loop to per_symbol
per_symbol_interfaces = [
    'cyq_perf',  # R4 stock_special fix
]

# Delete ALL sync_state for these interfaces (stale scope_keys from old strategy)
all_changed = full_once_interfaces + per_symbol_interfaces
for name in all_changed:
    result = ch_client.query(
        f"SELECT count() FROM _meta.sync_state WHERE interface = '{name}'"
    )
    cnt = result.result_rows[0][0]
    if cnt > 0:
        ch_client.command(
            f"ALTER TABLE _meta.sync_state DELETE WHERE interface = '{name}'"
        )
        print(f"  {name}: deleted {cnt} stale entries")

# Also clean up disabled interfaces with stale failures
disabled_interfaces = ['fund_div', 'cb_price_chg', 'cb_share']
for name in disabled_interfaces:
    result = ch_client.query(
        f"SELECT count() FROM _meta.sync_state WHERE interface = '{name}' AND status != 'done'"
    )
    cnt = result.result_rows[0][0]
    if cnt > 0:
        ch_client.command(
            f"ALTER TABLE _meta.sync_state DELETE WHERE interface = '{name}' AND status != 'done'"
        )
        print(f"  {name}: deleted {cnt} stale non-done entries")

# =============================================================================
# Step 2: Run the fixed full_once interfaces
# =============================================================================
print("\n=== Step 2: Running fixed full_once interfaces ===")

specs = load_interface_specs()
enabled_specs = [s for s in specs if s.enabled]

run_id = uuid.uuid4()
full_once_names = set(full_once_interfaces)
full_once_specs = [s for s in enabled_specs if s.name in full_once_names]
print(f"Full-once interfaces: {len(full_once_specs)}")

for spec in full_once_specs:
    units = plan_units(spec, ch_client)
    print(f"  {spec.name}: {len(units)} units")
    if units:
        execute_batch(units, tushare_client, ch_client, run_id=run_id)

# =============================================================================
# Step 3: Run cyq_perf with per_symbol
# =============================================================================
print("\n=== Step 3: Running cyq_perf with per_symbol ===")

per_symbol_names = set(per_symbol_interfaces)
per_symbol_specs = [s for s in enabled_specs if s.name in per_symbol_names]
for spec in per_symbol_specs:
    units = plan_units(spec, ch_client)
    print(f"  {spec.name}: {len(units)} units")
    if units:
        execute_batch(units, tushare_client, ch_client, run_id=run_id)

# =============================================================================
# Step 4: Retry small-failure interfaces
# =============================================================================
print("\n=== Step 4: Retrying small-failure interfaces ===")

# Reset failed units to pending for interfaces with transient errors
retry_names = {
    'fund_nav',       # 22 SSL timeouts
    'fund_factor_pro',  # 8 SSL timeouts
    'stk_rewards',    # 3 date type errors
    'stock_company',  # 1 error
    'fund_company',   # 1 error
    'etf_index',      # 1 error
    'stk_managers',   # 1 error
    'index_basic',    # 1 error
}

now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
version = int(now.timestamp() * 1000)

for name in sorted(retry_names):
    result = ch_client.query(f"""
        SELECT count() FROM _meta.sync_state
        WHERE interface = '{name}' AND status = 'failed'
    """)
    cnt = result.result_rows[0][0]
    if cnt > 0:
        ch_client.command(f"""
            INSERT INTO _meta.sync_state
            SELECT
                interface, scope_key,
                'pending' as status,
                0 as rows,
                toDateTime64('1970-01-01 00:00:00', 9, 'UTC') as last_success_at,
                toDateTime64('1970-01-01 00:00:00', 9, 'UTC') as heartbeat_at,
                attempts as attempts,
                '' as last_error,
                {version} as _version
            FROM _meta.sync_state
            WHERE interface = '{name}' AND status = 'failed'
        """)
        print(f"  {name}: reset {cnt} failed units to pending")

# =============================================================================
# Step 5: Re-plan and execute retry interfaces
# =============================================================================
print("\n=== Step 5: Executing retry interfaces ===")

retry_specs = [s for s in enabled_specs if s.name in retry_names]
for spec in retry_specs:
    units = plan_units(spec, ch_client)
    # Only process non-done units (planner already creates all, but we need pending only)
    pending_units = []
    for u in units:
        result = ch_client.query(f"""
            SELECT count() FROM _meta.sync_state
            WHERE interface = '{u.interface}'
              AND scope_key = '{u.scope_key}'
              AND status = 'done'
        """)
        if result.result_rows[0][0] == 0:
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
result = ch_client.query(
    "SELECT status, count() FROM _meta.sync_state GROUP BY status ORDER BY status"
)
print("Sync state:")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]}")

tushare_client.close()
ch_client.close()
print("\nResume R4 complete.")
