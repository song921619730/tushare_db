"""Create a missing CH table from PG schema."""
import sys
sys.path.insert(0, "src")

import clickhouse_connect
import psycopg
from tushare_db.migration.type_mapper import pg_type_to_ch

table = sys.argv[1]

conn = psycopg.connect(host='localhost', port=5432, user='market_user', password='market_password', dbname='market_db')
with conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table,))
    cols = cur.fetchall()
conn.close()

ch_defs = []
for name, pg_type, nullable in cols:
    if name in ('created_at', 'updated_at'):
        continue
    ch_type = pg_type_to_ch(pg_type, name)
    if nullable == 'YES' and not ch_type.startswith('LowCardinality'):
        ch_type = f"Nullable({ch_type})"
    ch_defs.append(f"    {name} {ch_type}")
ch_defs.append("    _version UInt64")

has_ts_code = any(c[0] == 'ts_code' for c in cols)
has_trade_date = any(c[0] == 'trade_date' for c in cols)

if has_ts_code and has_trade_date:
    order_by = "(ts_code, trade_date)"
    partition_by = "toYYYYMM(trade_date)"
elif has_trade_date:
    order_by = f"({cols[0][0]}, trade_date)"
    partition_by = "toYYYYMM(trade_date)"
else:
    order_by = "tuple()"
    partition_by = "tuple()"

cols_str = ",\n".join(ch_defs)
ddl = f"""CREATE TABLE IF NOT EXISTS tushare.{table} (
{cols_str}
) ENGINE = ReplacingMergeTree(_version)
PARTITION BY {partition_by}
ORDER BY {order_by}"""

print(f"Creating tushare.{table}...")
ch = clickhouse_connect.get_client(
    host='localhost', port=8123, username='pipeline',
    password='wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E',
    database='tushare'
)
ch.command(ddl)

cols_result = ch.query(
    f"SELECT name, type FROM system.columns "
    f"WHERE database='tushare' AND table='{table}' ORDER BY position"
)
print(f"Table created with {len(cols_result.result_rows)} columns:")
for name, dtype in cols_result.result_rows:
    print(f"  {name}: {dtype}")
