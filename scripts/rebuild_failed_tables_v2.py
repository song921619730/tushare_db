"""Rebuild 4 tables with ts_code-only sort key."""

import psycopg
import clickhouse_connect

pwd = 'wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E'

pg_conn = psycopg.connect(
    host='localhost', port=5432, user='market_user',
    password='market_password', dbname='market_db'
)
cur = pg_conn.cursor()

tables = ['tushare_fund_basic', 'tushare_stock_company', 'tushare_etf_basic', 'tushare_index_basic', 'tushare_cb_basic']

ch_client = clickhouse_connect.get_client(
    host='localhost', port=8123, username='pipeline', password=pwd, database='tushare'
)

def pg_to_ch(col_info, is_key=False):
    col_name, data_type, num_prec, num_scale, char_max, udt_name = col_info
    if data_type in ("character varying", "text", "character"):
        return "String" if is_key else "Nullable(String)"
    elif data_type == "integer":
        return "Int32" if is_key else "Nullable(Int32)"
    elif data_type == "bigint":
        return "Int64" if is_key else "Nullable(Int64)"
    elif data_type in ("numeric", "decimal"):
        prec = num_prec or 18
        scale = num_scale or 2
        return f"Decimal({prec}, {scale})" if is_key else f"Nullable(Decimal({prec}, {scale}))"
    elif data_type == "double precision":
        return "Float64" if is_key else "Nullable(Float64)"
    elif data_type == "date":
        return "Date" if is_key else "Nullable(Date)"
    elif data_type.startswith("timestamp"):
        return "DateTime" if is_key else "Nullable(DateTime)"
    return "String" if is_key else "Nullable(String)"

for table in tables:
    cur.execute("""
        SELECT column_name, data_type, numeric_precision, numeric_scale,
               character_maximum_length, udt_name
        FROM information_schema.columns
        WHERE table_name = %s ORDER BY ordinal_position
    """, (table,))
    cols = [c for c in cur.fetchall() if c[0] not in ("created_at", "updated_at")]

    ch_client.command(f"DROP TABLE IF EXISTS tushare.{table}")

    col_defs = []
    for c in cols:
        is_key = (c[0] == "ts_code")
        ch_type = pg_to_ch(c, is_key=is_key)
        col_defs.append(f"    `{c[0]}` {ch_type}")
    col_defs.append("    `_version` UInt64")

    create_sql = f"""CREATE TABLE tushare.{table}
(
{",\n".join(col_defs)}
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY (ts_code)
SETTINGS index_granularity = 8192"""

    try:
        ch_client.command(create_sql)
        print(f"  OK: {table}")
    except Exception as e:
        print(f"  FAIL: {table}: {e}")

pg_conn.close()
ch_client.close()
print("Done")
