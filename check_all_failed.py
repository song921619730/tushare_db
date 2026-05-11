"""Check all failed interfaces and categorize root causes."""
import os, sys
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

# Get all interfaces with failed records
result = ch.query("""
    SELECT interface, status, last_error
    FROM _meta.sync_state
    WHERE status IN ('failed', 'biz_err', 'partial')
    GROUP BY interface, status, last_error
    ORDER BY interface
""")

rows = result.result_rows
print(f"Total failed/biz_err/partial records: {len(rows)}")
print(f"{'Interface':<30} {'Status':<12} {'Error'}")
print("-" * 120)
for row in rows:
    iface, status, error = row[0], row[1], row[2][:150] if row[2] else ''
    print(f"{iface:<30} {status:<12} {error}")

# Summary: count by interface
print("\n--- Summary by interface ---")
result2 = ch.query("""
    SELECT interface, status, count()
    FROM _meta.sync_state
    WHERE status IN ('failed', 'biz_err', 'partial')
    GROUP BY interface, status
    ORDER BY interface
""")
for row in result2.result_rows:
    print(f"  {row[0]}: {row[1]} x {row[2]}")

ch.close()
