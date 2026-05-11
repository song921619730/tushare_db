"""Resume all fixed interfaces after schema, strategy, and table fixes."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_all_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

print(f"Resume all fixed interfaces starting... PID={os.getpid()}")

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

# Load all enabled specs
specs = load_interface_specs()
enabled_specs = [s for s in specs if s.enabled]
print(f"Total enabled interfaces: {len(enabled_specs)}")

# Filter to just the ones we fixed
fixed_names = {
    # Schema mismatch (11)
    'cb_basic', 'cn_cpi', 'cn_m', 'cn_ppi', 'etf_basic', 'fut_daily',
    'hibor', 'index_basic', 'libor', 'margin', 'stock_company',
    # Missing tables (5)
    'dc_hot', 'moneyflow_cnt_ths', 'moneyflow_ind_ths', 'moneyflow_ths', 'stk_ah_comparison',
    # Missing params (8)
    'broker_recommend', 'cyq_chips', 'index_daily', 'pledge_detail',
    'stk_rewards', 'stk_week_month_adj', 'stk_weekly_monthly', 'fut_weekly_monthly',
    # Network timeouts (3)
    'dc_member', 'share_float', 'stk_holdernumber',
    # Processing errors (15)
    'cn_pmi', 'stk_nineturn', 'stk_managers', 'cb_share', 'ccass_hold',
    'fund_basic', 'fund_company', 'fund_factor_pro', 'fund_div', 'fund_nav', 'fund_portfolio',
    'etf_index', 'index_weight', 'ths_hot', 'cb_price_chg',
    # Validation failures (2)
    'dividend', 'forecast',
}

fixed_specs = [s for s in enabled_specs if s.name in fixed_names]
print(f"Fixed interfaces to resume: {len(fixed_specs)}")
print(f"Names: {[s.name for s in fixed_specs]}")

run_id = uuid.uuid4()
total_units = 0
total_done = 0
total_failed = 0

for spec in fixed_specs:
    units = plan_units(spec, ch_client)
    if not units:
        print(f"  {spec.name}: no work units")
        continue

    total_units += len(units)
    print(f"  {spec.name}: {len(units)} units")

    done, done_count, failed_count = execute_batch(
        units, tushare_client, ch_client, run_id=run_id,
    )
    total_done += done_count
    total_failed += failed_count
    print(f"    -> done={done_count}, failed={failed_count}")

print(f"\nResume complete: {total_units} units, {total_done} done, {total_failed} failed")

tushare_client.close()
ch_client.close()
