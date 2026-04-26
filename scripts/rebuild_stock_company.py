"""Rebuild stock_company and index_basic with ts_code only sort key."""

import psycopg
import clickhouse_connect

pwd = 'wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E'

pg_conn = psycopg.connect(
    host='localhost', port=5432, user='market_user',
    password='market_password', dbname='market_db'
)
cur = pg_conn.cursor()

ch_client = clickhouse_connect.get_client(
    host='localhost', port=8123, username='pipeline', password=pwd, database='tushare'
)

for table in ['tushare_stock_company', 'tushare_index_basic']:
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
        if is_key:
            ch_type = "String"
        elif c[1] in ("character varying", "text", "character"):
            ch_type = "Nullable(String)"
        elif c[1] == "integer":
            ch_type = "Nullable(Int32)"
        elif c[1] == "bigint":
            ch_type = "Nullable(Int64)"
        elif c[1] in ("numeric", "decimal"):
            p = c[2] or 18
            s = c[3] or 2
            ch_type = f"Nullable(Decimal({p}, {s}))"
        elif c[1] == "double precision":
            ch_type = "Nullable(Float64)"
        elif c[1] == "date":
            ch_type = "Nullable(Date)"
        elif c[1].startswith("timestamp"):
            ch_type = "Nullable(DateTime)"
        else:
            ch_type = "Nullable(String)"
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
