"""Check sync state and data freshness as of 2026-05-06."""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from tushare_db.sink.clickhouse_sink import get_native_client

ch = get_native_client(
    host=os.environ.get('CH_HOST', 'localhost'),
    port=8123,
    user='pipeline',
    password=os.environ.get('CH_PIPELINE_PASSWORD', '')
)

today = '20260506'
# The last trading day before May 6 (Wednesday) - May 5 is Tuesday, likely a trading day
# Let's check the last few trading days
print("=" * 80)
print("  Data Freshness Report as of 2026-05-06 (Wednesday)")
print("=" * 80)

# 1. Check trade_cal for recent trading days
print("\n--- Recent Trading Days ---")
result = ch.query("""
    SELECT cal_date, is_open
    FROM _meta.trade_cal
    WHERE cal_date >= '20260428' AND cal_date <= '20260508'
    ORDER BY cal_date
""")
for row in result.result_rows:
    status = 'OPEN' if row[1] == 1 else 'CLOSED'
    print(f"  {row[0]}: {status}")

# 2. Check sync_state for the latest trading day (assume 20260505 is last trading day)
print("\n--- Sync State for 2026-05-05 (latest possible trading day) ---")
result = ch.query("""
    SELECT interface, status, count(), sum(rows) as total_rows
    FROM _meta.sync_state FINAL
    WHERE scope_key LIKE '%20260505%'
    GROUP BY interface, status
    ORDER BY interface, status
""")
if result.result_rows:
    iface_status = {}
    for row in result.result_rows:
        iface = row[0]
        if iface not in iface_status:
            iface_status[iface] = []
        iface_status[iface].append({'status': row[1], 'count': row[2], 'rows': row[3]})
    for iface, statuses in sorted(iface_status.items()):
        status_str = ', '.join([f"{s['status']}({s['count']}u, {s['rows']}r)" for s in statuses])
        print(f"  {iface}: {status_str}")
else:
    print("  No sync records for 20260505")

# 3. Check overall sync_state summary
print("\n--- Overall Sync State Summary ---")
result = ch.query("""
    SELECT status, count() as cnt, sum(rows) as total_rows
    FROM _meta.sync_state FINAL
    GROUP BY status
    ORDER BY status
""")
for row in result.result_rows:
    print(f"  {row[0]}: {row[1]} units, {row[2]} total rows")

# 4. Check recent sync_runs
print("\n--- Recent Sync Runs (last 10) ---")
result = ch.query("""
    SELECT run_id, interface, start_time, end_time, status, rows_synced
    FROM _meta.sync_runs
    ORDER BY start_time DESC
    LIMIT 10
""")
if result.result_rows:
    for row in result.result_rows:
        print(f"  {row[0][:8]}... | {row[1]} | {row[2]} -> {row[3]} | {row[4]} | {row[5]} rows")
else:
    print("  No sync runs found")

# 5. Check for failed/pending units
print("\n--- Failed / Pending / Biz Error Units ---")
result = ch.query("""
    SELECT interface, status, count() as cnt
    FROM _meta.sync_state FINAL
    WHERE status IN ('failed', 'pending', 'biz_err', 'partial')
    GROUP BY interface, status
    ORDER BY interface, status
""")
if result.result_rows:
    for row in result.result_rows:
        print(f"  {row[0]}: {row[1]} ({row[2]} units)")
else:
    print("  No failed/pending/biz_err units found")

ch.close()
