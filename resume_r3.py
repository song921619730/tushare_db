"""Resume round 3: fix macro interfaces (cn_cpi, cn_m, cn_ppi, hibor, libor).
These were wrongly configured as date_loop but should be full_once.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_r3_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

print(f"Resume R3: macro interfaces starting... PID={os.getpid()}")

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

# 5 macro interfaces fixed to full_once
macro_names = {'cn_cpi', 'cn_m', 'cn_ppi', 'hibor', 'libor'}

specs = load_interface_specs()
enabled_specs = [s for s in specs if s.enabled]
macro_specs = [s for s in enabled_specs if s.name in macro_names]

print(f"Macro interfaces: {[s.name for s in macro_specs]}")
for s in macro_specs:
    print(f"  {s.name}: fetch_strategy={s.fetch_strategy.kind}")

run_id = uuid.uuid4()
total_units = 0
total_done = 0
total_failed = 0

for spec in macro_specs:
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

print(f"\nResume R3 complete: {total_units} units, {total_done} done, {total_failed} failed")

tushare_client.close()
ch_client.close()
