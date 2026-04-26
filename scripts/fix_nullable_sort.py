"""Fix tables with nullable sort keys."""

import clickhouse_connect

CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "pipeline"
CH_PASSWORD = "wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E"

ch_client = clickhouse_connect.get_client(
    host=CH_HOST, port=CH_PORT, username=CH_USER,
    password=CH_PASSWORD, database="tushare"
)

# Drop and recreate the 3 failed tables
tables_to_fix = {
    "tushare_index_weight": {
        "cols": [
            ("ts_code", "String"),
            ("index_code", "Nullable(String)"),
            ("trade_date", "Date"),
            ("con_code", "Nullable(String)"),
            ("weight", "Nullable(Float64)"),
        ],
        "order_by": "ts_code, trade_date",
    },
    "tushare_stock_monthly": {
        "cols": [
            ("ts_code", "String"),
            ("trade_date", "Date"),
            ("open", "Nullable(Float64)"),
            ("high", "Nullable(Float64)"),
            ("low", "Nullable(Float64)"),
            ("close", "Nullable(Float64)"),
            ("vol", "Nullable(Float64)"),
            ("amount", "Nullable(Float64)"),
            ("pct_chg", "Nullable(Float64)"),
            ("turnover", "Nullable(Float64)"),
            ("switch_date", "Nullable(Date)"),
            ("accumulated_nav", "Nullable(Float64)"),
            ("total_return", "Nullable(Float64)"),
        ],
        "order_by": "ts_code, trade_date",
    },
    "tushare_index_daily": {
        "cols": [
            ("ts_code", "String"),
            ("trade_date", "Date"),
            ("close", "Nullable(Float64)"),
            ("open", "Nullable(Float64)"),
            ("high", "Nullable(Float64)"),
            ("low", "Nullable(Float64)"),
            ("pre_close", "Nullable(Float64)"),
            ("change", "Nullable(Float64)"),
            ("pct_chg", "Nullable(Float64)"),
            ("vol", "Nullable(Float64)"),
            ("amount", "Nullable(Float64)"),
        ],
        "order_by": "ts_code, trade_date",
    },
}

for table_name, spec in tables_to_fix.items():
    # Drop existing
    ch_client.command(f"DROP TABLE IF EXISTS tushare.{table_name}")

    col_defs = [f"    `{c[0]}` {c[1]}" for c in spec["cols"]]
    col_defs.append("    `_version` UInt64")

    create_sql = f"""CREATE TABLE tushare.{table_name}
(
{",\n".join(col_defs)}
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY ({spec['order_by']})
SETTINGS index_granularity = 8192"""

    ch_client.command(create_sql)
    print(f"  OK: {table_name}")

ch_client.close()
print("Done!")
