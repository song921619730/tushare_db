"""Resume script for per_symbol interfaces: stk_holdernumber, pledge_stat, repurchase, share_float."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
log_file = f"logs/resume_per_symbol_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, 'w', encoding='utf-8')
sys.stderr = sys.stdout

from tushare_db.sink.clickhouse_sink import get_native_client
from tushare_db.core.tushare_client import TushareClient
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.config.loader import load_interface_specs
from tushare_db.runner.backfill import run_backfill
from tushare_db.core.concurrency_lock import ConcurrencyLock
import uuid

print(f"Resume per_symbol starting... PID={os.getpid()}")

lock = ConcurrencyLock()
lock.acquire()

TARGET = {'stk_holdernumber', 'pledge_stat', 'repurchase', 'share_float'}

ch_client = get_native_client(
    host=os.environ.get('CH_HOST', 'localhost'),
    port=8123,
    user='pipeline',
    password=os.environ.get('CH_PIPELINE_PASSWORD', '')
)
token = os.environ['TUSHARE_TOKEN']
limiter = DualRateLimiter(normal_rpm=475, special_rpm=285)
tushare_client = TushareClient(token=token, limiter=limiter)

specs = [s for s in load_interface_specs() if s.name in TARGET]
print(f"Interfaces to backfill: {[s.name for s in specs]}")

summary = run_backfill(specs, tushare_client, ch_client, verify_hook=None)
print(f"\nBackfill complete: {summary}")

tushare_client.close()
ch_client.close()
