"""Run fina_audit backfill."""
import os, sys
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_script_dir, "..", "src"))

# Load .env
env_path = os.path.join(_script_dir, "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

os.makedirs("logs", exist_ok=True)
log_file = f"logs/fina_audit_run_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = open(log_file, "w", encoding="utf-8")
sys.stderr = sys.stdout

print(f"fina_audit backfill starting... PID={os.getpid()}")
print(f"Log file: {log_file}")
print(f"CH_HOST: {os.environ.get('CH_HOST', 'localhost')}")
print(f"CH_PIPELINE_PASSWORD: {os.environ.get('CH_PIPELINE_PASSWORD', 'NOT SET')[:10]}...")

import clickhouse_connect
from tushare_db.config.loader import load_interface_specs
from tushare_db.core.concurrency_lock import ConcurrencyLock
from tushare_db.core.rate_limiter import DualRateLimiter
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch

lock = ConcurrencyLock()
lock.acquire()

ch = clickhouse_connect.get_client(
    host="localhost",
    port=8123, user="pipeline",
    password="wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E",
    database="tushare",
)

limiter = DualRateLimiter(normal_rpm=475, special_rpm=15)
ts = TushareClient(token=os.environ["TUSHARE_TOKEN"], limiter=limiter)

specs = load_interface_specs()
spec = next(s for s in specs if s.name == "fina_audit")

print(f"Interface: {spec.name}")
print(f"Strategy: {spec.fetch_strategy.kind}")
print(f"Bucket: {spec.freq_bucket}")

# Clear stale sync_state
print("Clearing stale sync_state...")
ch.command("ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fina_audit'")

import time
time.sleep(3)

print("Planning work units...")
units = plan_units(spec, ch)
print(f"Planned {len(units)} work units")

# Run with 2 special workers (reduced from 4 to avoid rate limiter contention at 15 RPM)
os.environ["TUSHARE_SPECIAL_WORKERS"] = "2"
os.environ["TUSHARE_NORMAL_WORKERS"] = "0"

print(f"Executing {len(units)} units with 2 special workers...")
total, done, failed = execute_batch(units, ts, ch)
print(f"\nResult: {total} total, {done} done, {failed} failed")

ts.close()
ch.close()
lock.release()
print("Done!")
