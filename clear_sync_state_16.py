"""Delete failed sync_state records and re-trigger backfill for 16 interfaces."""
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

interfaces = [
    'cb_basic', 'cn_cpi', 'cn_m', 'cn_ppi', 'etf_basic', 'fut_daily',
    'hibor', 'index_basic', 'libor', 'margin', 'stock_company',
    'dc_hot', 'moneyflow_cnt_ths', 'moneyflow_ind_ths', 'moneyflow_ths', 'stk_ah_comparison'
]

# Delete ALL sync_state records for these interfaces
for iface in interfaces:
    try:
        ch.command(f"DELETE FROM _meta.sync_state WHERE interface = '{iface}'")
        print(f'Deleted sync_state records for: {iface}')
    except Exception as e:
        print(f'ERR: {iface} -> {e}')

print('\nDone. Tables are created and sync_state cleared for these interfaces.')
print('Now run: tushare-db backfill --interface <name> for each interface')
ch.close()
