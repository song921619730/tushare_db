"""Check details of running records."""
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

result = ch.query("""
    SELECT interface, scope_key, attempts, heartbeat_at, last_success_at, last_error
    FROM _meta.sync_state
    WHERE status = 'running'
    ORDER BY interface, scope_key
""")

print(f'Running records: {len(result.result_rows)}')
print()
print(f'{"Interface":<15} {"Scope Key":<60} {"Attempts":<10} {"Heartbeat":<28} {"Last Success":<28} {"Error"}')
print('-' * 180)
for row in result.result_rows:
    iface, scope_key, attempts, heartbeat_at, last_success_at, last_error = row
    err = str(last_error)[:60] if last_error else ''
    print(f'{iface:<15} {scope_key:<60} {attempts:<10} {heartbeat_at:<28} {last_success_at:<28} {err}')

ch.close()
