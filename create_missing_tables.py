"""Create 5 missing tables."""
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

# Table definitions based on sample fields
table_defs = [
    {
        'name': 'dc_hot',
        'fields': [
            ('trade_date', 'Date'),
            ('ts_code', 'String'),
            ('name', 'Nullable(String)'),
            ('lead_stock', 'Nullable(String)'),
            ('close_price', 'Nullable(Decimal(10, 2))'),
            ('pct_change', 'Nullable(Decimal(10, 2))'),
            ('industry_index', 'Nullable(String)'),
            ('company_num', 'Nullable(Decimal(18, 2))'),
            ('pct_change_stock', 'Nullable(Decimal(10, 2))'),
            ('net_buy_amount', 'Nullable(Decimal(18, 2))'),
            ('net_sell_amount', 'Nullable(Decimal(18, 2))'),
            ('net_amount', 'Nullable(Decimal(18, 2))'),
        ],
        'partition_key': 'toYYYYMM(trade_date)',
        'order_by': ('ts_code', 'trade_date'),
    },
    {
        'name': 'moneyflow_cnt_ths',
        'fields': [
            ('trade_date', 'Date'),
            ('ts_code', 'String'),
            ('name', 'Nullable(String)'),
            ('pct_change', 'Nullable(Decimal(10, 2))'),
            ('latest', 'Nullable(Decimal(18, 2))'),
            ('net_amount', 'Nullable(Decimal(18, 2))'),
            ('net_d5_amount', 'Nullable(Decimal(18, 2))'),
            ('buy_lg_amount', 'Nullable(Decimal(18, 2))'),
            ('buy_lg_amount_rate', 'Nullable(Decimal(10, 4))'),
            ('buy_md_amount', 'Nullable(Decimal(18, 2))'),
            ('buy_md_amount_rate', 'Nullable(Decimal(10, 4))'),
            ('buy_sm_amount', 'Nullable(Decimal(18, 2))'),
            ('buy_sm_amount_rate', 'Nullable(Decimal(10, 4))'),
        ],
        'partition_key': 'toYYYYMM(trade_date)',
        'order_by': ('ts_code', 'trade_date'),
    },
    {
        'name': 'moneyflow_ind_ths',
        'fields': [
            ('trade_date', 'Date'),
            ('data_type', 'Nullable(String)'),
            ('ts_code', 'String'),
            ('ts_name', 'Nullable(String)'),
            ('rank', 'Nullable(Decimal(18, 2))'),
            ('pct_change', 'Nullable(Decimal(10, 2))'),
            ('current_price', 'Nullable(Decimal(10, 2))'),
            ('hot', 'Nullable(Decimal(18, 2))'),
            ('concept', 'Nullable(String)'),
            ('rank_time', 'Nullable(Date)'),
        ],
        'partition_key': 'toYYYYMM(trade_date)',
        'order_by': ('trade_date', 'ts_code'),
    },
    {
        'name': 'moneyflow_ths',
        'fields': [
            ('trade_date', 'Date'),
            ('ts_code', 'String'),
            ('industry', 'Nullable(String)'),
            ('lead_stock', 'Nullable(String)'),
            ('close', 'Nullable(Decimal(10, 2))'),
            ('pct_change', 'Nullable(Decimal(10, 2))'),
            ('company_num', 'Nullable(Decimal(18, 2))'),
            ('pct_change_stock', 'Nullable(Decimal(10, 2))'),
            ('close_price', 'Nullable(Decimal(10, 2))'),
            ('net_buy_amount', 'Nullable(Decimal(18, 2))'),
            ('net_sell_amount', 'Nullable(Decimal(18, 2))'),
            ('net_amount', 'Nullable(Decimal(18, 2))'),
        ],
        'partition_key': 'toYYYYMM(trade_date)',
        'order_by': ('ts_code', 'trade_date'),
    },
    {
        'name': 'stk_ah_comparison',
        'fields': [
            ('hk_code', 'String'),
            ('ts_code', 'String'),
            ('trade_date', 'Date'),
            ('hk_name', 'Nullable(String)'),
            ('hk_pct_chg', 'Nullable(Decimal(10, 2))'),
            ('hk_close', 'Nullable(Decimal(10, 2))'),
            ('name', 'Nullable(String)'),
            ('close', 'Nullable(Decimal(10, 2))'),
            ('pct_chg', 'Nullable(Decimal(10, 2))'),
            ('ah_comparison', 'Nullable(Decimal(10, 2))'),
            ('ah_premium', 'Nullable(Decimal(10, 2))'),
        ],
        'partition_key': 'toYYYYMM(trade_date)',
        'order_by': ('ts_code', 'trade_date'),
    },
]

for tdef in table_defs:
    name = tdef['name']
    table = f'tushare.tushare_{name}'
    fields_str = ', '.join(f'{f[0]} {f[1]}' for f in tdef['fields'])
    order_str = ', '.join(tdef['order_by'])

    sql = (
        f"CREATE TABLE IF NOT EXISTS {table} "
        f"({fields_str}, _version UInt64) "
        f"ENGINE = ReplacingMergeTree(_version) "
        f"PARTITION BY {tdef['partition_key']} "
        f"ORDER BY ({order_str})"
    )

    try:
        ch.command(sql)
        print(f'CREATED: {table}')
    except Exception as e:
        print(f'ERR: {table} -> {e}')

ch.close()
