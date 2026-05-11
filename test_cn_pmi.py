"""Test cn_pmi processing to understand the timestamp error."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient, DualRateLimiter
from tushare_db.core.concurrency_lock import ConcurrencyLock

lock = ConcurrencyLock()
lock.acquire()

ch = get_native_client(
    host=os.environ.get('CH_HOST', 'localhost'),
    port=8123,
    user='pipeline',
    password=os.environ.get('CH_PIPELINE_PASSWORD', '')
)
token = os.environ['TUSHARE_TOKEN']
limiter = DualRateLimiter(normal_rpm=475, special_rpm=285)
tc = TushareClient(token=token, limiter=limiter)

# Try cn_pmi via backfill
from tushare_db.config.loader import load_interface_specs
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch

specs = {s.name: s for s in load_interface_specs()}
for name in ['cn_pmi', 'ths_hot']:
    spec = specs.get(name)
    if not spec:
        print(f'{name}: NOT FOUND in specs')
        continue

    print(f'\n=== {name} ===')
    print(f'  strategy: {spec.fetch_strategy.kind}')
    print(f'  table: {spec.table}')

    units = plan_units(spec, ch)
    print(f'  units: {len(units)}')
    if units:
        print(f'  first unit: {units[0].scope_key}, params={units[0].params}')

        import uuid
        done, done_count, failed_count = execute_batch(
            units[:2], tc, ch, run_id=uuid.uuid4(),
        )
        print(f'  result: done={done_count}, failed={failed_count}')

tc.close()
ch.close()
