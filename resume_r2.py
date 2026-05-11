"""Resume round 2: retry tables that were just created and schema fixes applied."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_r2_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.core.concurrency_lock import ConcurrencyLock
import clickhouse_connect
import uuid

print(f"Resume round 2 starting... PID={os.getpid()}")

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

# Interfaces to retry in this round
# Tables just created: stk_week_month_adj, stk_weekly_monthly, fut_weekly_monthly
# Schema fixes applied: cn_ppi, etf_basic, fund_basic, stock_company
# Single SSL timeout retries: cb_share, fund_portfolio, fund_nav, fund_factor_pro, fut_weekly_monthly
# Other retries: stk_rewards, stk_managers, fund_company, index_basic, index_weight, etf_index
retry_names = {
    'stk_week_month_adj', 'stk_weekly_monthly', 'fut_weekly_monthly',
    'cn_ppi', 'etf_basic', 'fund_basic', 'stock_company',
    'stk_rewards', 'stk_managers', 'fund_company', 'index_basic',
    'index_weight', 'etf_index', 'fund_nav', 'fund_factor_pro',
    'fund_portfolio', 'cb_share',
}

# Reset failed units to pending for retry interfaces
print("Resetting failed units to pending...")
now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
version = int(now.timestamp() * 1000)
epoch = __import__('datetime').datetime(1970, 1, 1, tzinfo=__import__('datetime').timezone.utc)

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
                attempts + 1 as attempts,
                '' as last_error,
                {version} as _version
            FROM _meta.sync_state
            WHERE interface = '{name}' AND status = 'failed'
        """)
        print(f"  {name}: reset {cnt} failed units to pending")

# Load all enabled specs
specs = load_interface_specs()
enabled_specs = [s for s in specs if s.enabled]
print(f"\nTotal enabled interfaces: {len(enabled_specs)}")

# Filter to retry interfaces
retry_specs = [s for s in enabled_specs if s.name in retry_names]
print(f"Retry interfaces: {len(retry_specs)}")
print(f"Names: {[s.name for s in retry_specs]}")

run_id = uuid.uuid4()
total_units = 0
total_done = 0
total_failed = 0

for spec in retry_specs:
    units = plan_units(spec, ch_client)
    # Only retry pending/failed units
    pending_units = [u for u in units if True]  # planner already filters
    if not pending_units:
        print(f"  {spec.name}: no work units")
        continue

    total_units += len(pending_units)
    print(f"  {spec.name}: {len(pending_units)} units")

    done, done_count, failed_count = execute_batch(
        pending_units, tushare_client, ch_client, run_id=run_id,
    )
    total_done += done_count
    total_failed += failed_count
    print(f"    -> done={done_count}, failed={failed_count}")

print(f"\nResume R2 complete: {total_units} units, {total_done} done, {total_failed} failed")

tushare_client.close()
ch_client.close()
