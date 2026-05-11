"""Check overall sync state across all interfaces."""
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

# Overall status summary
result = ch.query("""
    SELECT status, count() as cnt, count(DISTINCT interface) as interfaces
    FROM _meta.sync_state
    GROUP BY status
    ORDER BY status
""")
print('=== Overall Sync State ===')
print(f'{"Status":<15} {"Records":<12} {"Interfaces"}')
print('-' * 50)
for row in result.result_rows:
    print(f'{row[0]:<15} {row[1]:<12} {row[2]}')

# Per-interface breakdown
result2 = ch.query("""
    SELECT interface,
           count() as total,
           sum(status = 'done') as done,
           sum(status = 'failed') as failed,
           sum(status = 'biz_err') as biz_err,
           sum(status = 'partial') as partial,
           sum(status = 'pending') as pending,
           sum(status = 'running') as running
    FROM _meta.sync_state
    GROUP BY interface
    ORDER BY interface
""")
print()
print('=== Per-Interface Status ===')
print(f'{"Interface":<30} {"Total":<8} {"Done":<8} {"Failed":<8} {"BizErr":<8} {"Partial":<8} {"Pending":<8} {"Running":<8}')
print('-' * 110)
for row in result2.result_rows:
    iface, total, done, failed, biz_err, partial, pending, running = row
    flag = ''
    if failed > 0 or biz_err > 0:
        flag = ' ***'
    elif partial > 0:
        flag = ' ~~~'
    elif pending > 0:
        flag = ' ---'
    print(f'{iface:<30} {total:<8} {done:<8} {failed:<8} {biz_err:<8} {partial:<8} {pending:<8} {running:<8}{flag}')

ch.close()
