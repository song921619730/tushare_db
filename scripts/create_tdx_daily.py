# -*- coding: utf-8 -*-
from clickhouse_connect import get_client

pw = 'wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E'
ch = get_client(host='localhost', port=8123, user='pipeline', password=pw)

# tdx_daily fields from sample - all nullable since we have no sample data
columns = [
    ("ts_code", "LowCardinality(String)"),
    ("trade_date", "Date"),
    ("close", "Nullable(Float64)"),
    ("open", "Nullable(Float64)"),
    ("high", "Nullable(Float64)"),
    ("low", "Nullable(Float64)"),
    ("pre_close", "Nullable(Float64)"),
    ("change", "Nullable(Float64)"),
    ("pct_change", "Nullable(Float64)"),
    ("vol", "Nullable(Float64)"),
    ("amount", "Nullable(Float64)"),
    ("rise", "Nullable(Int64)"),
    ("vol_ratio", "Nullable(Float64)"),
    ("turnover_rate", "Nullable(Float64)"),
    ("swing", "Nullable(Float64)"),
    ("up_num", "Nullable(Int64)"),
    ("down_num", "Nullable(Int64)"),
    ("limit_up_num", "Nullable(Int64)"),
    ("limit_down_num", "Nullable(Int64)"),
    ("lu_days", "Nullable(Int64)"),
    ("3day", "Nullable(Float64)"),
    ("5day", "Nullable(Float64)"),
    ("10day", "Nullable(Float64)"),
    ("20day", "Nullable(Float64)"),
    ("60day", "Nullable(Float64)"),
    ("mtd", "Nullable(Float64)"),
    ("ytd", "Nullable(Float64)"),
    ("1year", "Nullable(Float64)"),
    ("pe", "Nullable(Float64)"),
    ("pb", "Nullable(Float64)"),
    ("float_mv", "Nullable(Float64)"),
    ("ab_total_mv", "Nullable(Float64)"),
    ("float_share", "Nullable(Float64)"),
    ("total_share", "Nullable(Float64)"),
    ("bm_buy_net", "Nullable(Float64)"),
    ("bm_buy_ratio", "Nullable(Float64)"),
    ("bm_net", "Nullable(Float64)"),
    ("bm_ratio", "Nullable(Float64)"),
    ("_version", "UInt64"),
]

col_lines = []
for name, ctype in columns:
    col_lines.append(f"    {name} {ctype}")

ddl = (
    "CREATE TABLE IF NOT EXISTS tushare.tushare_tdx_daily (\n"
    + ",\n".join(col_lines)
    + "\n) ENGINE = ReplacingMergeTree(_version)\n"
    "PARTITION BY toYYYYMM(trade_date)\n"
    "ORDER BY (ts_code, trade_date)"
)

print("Creating table tushare_tdx_daily...")
print(ddl)
ch.command(ddl)
print("Table created!")

# Verify
r = ch.query("SELECT name, type FROM system.columns WHERE database = 'tushare' AND table = 'tushare_tdx_daily' ORDER BY position")
for row in r.result_rows:
    print(f"  {row[0]}: {row[1]}")
print(f"Total columns: {len(r.result_rows)}")
