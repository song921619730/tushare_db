"""Delete failed/partial/biz_err sync_state records and re-trigger backfill."""
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

# All 16 interfaces that need attention
# 11 schema mismatch (fixed columns) + 5 newly created tables
interfaces = [
    'cb_basic', 'cn_cpi', 'cn_m', 'cn_ppi', 'etf_basic', 'fut_daily',
    'hibor', 'index_basic', 'libor', 'margin', 'stock_company',
    'dc_hot', 'moneyflow_cnt_ths', 'moneyflow_ind_ths', 'moneyflow_ths', 'stk_ah_comparison'
]

# Check current state for these interfaces
for iface in interfaces:
    try:
        # Count records by status
        result = ch.query(f"""
            SELECT status, count()
            FROM _meta.sync_state
            WHERE interface = '{iface}'
            GROUP BY status
            ORDER BY status
        """)
        counts = {row[0]: row[1] for row in result.result_rows}
        total = sum(counts.values())
        print(f'{iface}: total={total} {dict(counts)}')
    except Exception as e:
        print(f'{iface}: ERROR - {e}')

ch.close()
