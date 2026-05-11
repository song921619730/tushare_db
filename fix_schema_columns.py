"""Fix missing columns for 11 schema mismatch tables."""
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

# Each entry: (table, col, type)
# Note: columns starting with digit need special handling - use _12m pattern
alters = [
    # cb_basic
    ('tushare_cb_basic', 'bond_full_name', 'Nullable(String)'),
    ('tushare_cb_basic', 'cb_type', 'Nullable(String)'),
    ('tushare_cb_basic', 'cb_code', 'Nullable(String)'),
    ('tushare_cb_basic', 'stk_short_name', 'Nullable(String)'),
    ('tushare_cb_basic', 'par', 'Nullable(Decimal(10, 2))'),
    ('tushare_cb_basic', 'issue_price', 'Nullable(Decimal(10, 2))'),
    ('tushare_cb_basic', 'issue_size', 'Nullable(Decimal(18, 2))'),
    ('tushare_cb_basic', 'remain_size', 'Nullable(Decimal(18, 2))'),
    ('tushare_cb_basic', 'value_date', 'Nullable(Date)'),
    ('tushare_cb_basic', 'maturity_date', 'Nullable(Date)'),
    ('tushare_cb_basic', 'rate_type', 'Nullable(String)'),
    ('tushare_cb_basic', 'add_rate', 'Nullable(Decimal(6, 4))'),
    ('tushare_cb_basic', 'pay_per_year', 'Nullable(Decimal(6, 2))'),
    ('tushare_cb_basic', 'exchange', 'Nullable(String)'),
    ('tushare_cb_basic', 'conv_start_date', 'Nullable(Date)'),
    ('tushare_cb_basic', 'conv_end_date', 'Nullable(Date)'),
    ('tushare_cb_basic', 'conv_stop_date', 'Nullable(Date)'),
    ('tushare_cb_basic', 'first_conv_price', 'Nullable(Decimal(10, 2))'),
    ('tushare_cb_basic', 'conv_price', 'Nullable(Decimal(10, 2))'),
    ('tushare_cb_basic', 'rate_clause', 'Nullable(String)'),
    # cn_cpi
    ('tushare_cn_cpi', 'nt_val', 'Nullable(Decimal(18, 2))'),
    ('tushare_cn_cpi', 'nt_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'nt_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'nt_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'town_val', 'Nullable(Decimal(18, 2))'),
    ('tushare_cn_cpi', 'town_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'town_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'town_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'cnt_val', 'Nullable(Decimal(18, 2))'),
    ('tushare_cn_cpi', 'cnt_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'cnt_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_cpi', 'cnt_accu', 'Nullable(Decimal(8, 2))'),
    # cn_m
    ('tushare_cn_m', 'm1_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_m', 'm2_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_m', 'm0_mom', 'Nullable(Decimal(8, 2))'),
    # cn_ppi
    ('tushare_cn_ppi', 'ppi_mp_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_qm_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_rm_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_p_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_f_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_c_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_adu_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_dcg_yoy', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_qm_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_rm_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_p_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_f_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_c_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_adu_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_dcg_mom', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_qm_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_rm_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_mp_p_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_f_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_c_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_adu_accu', 'Nullable(Decimal(8, 2))'),
    ('tushare_cn_ppi', 'ppi_cg_dcg_accu', 'Nullable(Decimal(8, 2))'),
    # etf_basic
    ('tushare_etf_basic', 'csname', 'Nullable(String)'),
    ('tushare_etf_basic', 'extname', 'Nullable(String)'),
    ('tushare_etf_basic', 'cname', 'Nullable(String)'),
    ('tushare_etf_basic', 'index_code', 'Nullable(String)'),
    ('tushare_etf_basic', 'index_name', 'Nullable(String)'),
    ('tushare_etf_basic', 'list_status', 'Nullable(String)'),
    ('tushare_etf_basic', 'mgr_name', 'Nullable(String)'),
    ('tushare_etf_basic', 'custod_name', 'Nullable(String)'),
    ('tushare_etf_basic', 'mgt_fee', 'Nullable(Decimal(6, 4))'),
    ('tushare_etf_basic', 'etf_type', 'Nullable(String)'),
    # fut_daily
    ('tushare_fut_daily', 'pre_close', 'Nullable(Decimal(12, 4))'),
    # hibor - column named "12m" needs backtick quoting
    # libor - column named "12m" needs backtick quoting
    # margin
    ('tushare_margin', 'rqye', 'Nullable(Decimal(18, 4))'),
    # stock_company
    ('tushare_stock_company', 'com_id', 'Nullable(String)'),
    ('tushare_stock_company', 'introduction', 'Nullable(String)'),
]

ok_count = 0
err_count = 0
for table, col, col_type in alters:
    try:
        sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "{col}" {col_type}'
        ch.command(sql)
        print(f'OK: {table}.{col}')
        ok_count += 1
    except Exception as e:
        print(f'ERR: {table}.{col} -> {e}')
        err_count += 1

# Handle "12m" columns (digit prefix)
for table, col_name in [('tushare_hibor', '12m'), ('tushare_libor', '12m')]:
    try:
        sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "{col_name}" Nullable(Decimal(18, 4))'
        ch.command(sql)
        print(f'OK: {table}."{col_name}"')
        ok_count += 1
    except Exception as e:
        print(f'ERR: {table}."{col_name}" -> {e}')
        err_count += 1

print(f'\nDone: {ok_count} OK, {err_count} errors')
ch.close()
