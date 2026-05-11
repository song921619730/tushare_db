"""Standalone resume script: stk_holdernumber/pledge_stat/repurchase/share_float/dividend/forecast."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

# Redirect stdout/stderr to log file
os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch
from tushare_db.meta.sync_state import get_pending_units
from tushare_db.core.concurrency_lock import ConcurrencyLock
import uuid

print(f"Resume starting... PID={os.getpid()}")
print(f"Log file: {log_file}")

# Acquire lock
lock = ConcurrencyLock()
lock.acquire()

TARGET = ['stk_holdernumber', 'pledge_stat', 'repurchase', 'share_float', 'dividend', 'forecast']

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
specs = [s for s in specs if s.name in TARGET]

run_id = uuid.uuid4()
total_units = 0
total_done = 0
total_failed = 0

for spec in specs:
    pending = get_pending_units(ch_client, spec.name)
    if not pending:
        print(f"  {spec.name}: no pending units")
        continue

    # Count by status
    by_status = {}
    for u in pending:
        st = u['status']
        by_status[st] = by_status.get(st, 0) + 1
    status_str = ', '.join(f'{k}:{v}' for k, v in sorted(by_status.items()))
    print(f"  {spec.name}: {len(pending)} pending ({status_str})")

    # Re-plan units
    units = plan_units(spec, ch_client)
    if not units:
        continue

    # Filter to only pending scope_keys
    pending_keys = {u['scope_key'] for u in pending}
    pending_units = [u for u in units if u.scope_key in pending_keys]

    if not pending_units:
        print(f"    {spec.name}: no matching work units")
        continue

    total_units += len(pending_units)
    print(f"    {spec.name}: resuming {len(pending_units)} units")

    done, done_count, failed_count = execute_batch(
        pending_units, tushare_client, ch_client, run_id=run_id,
    )
    total_done += done_count
    total_failed += failed_count

print(f"\nResume complete: {total_units} units, {total_done} done, {total_failed} failed")

tushare_client.close()
ch_client.close()
