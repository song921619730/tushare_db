"""Direct SQL migration for tables with date serialization issues."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import time
import psycopg
import clickhouse_connect
from datetime import date

pwd = 'wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E'

pg_conn = psycopg.connect(
    host='localhost', port=5432, user='market_user',
    password='market_password', dbname='market_db'
)

ch_client = clickhouse_connect.get_client(
    host='localhost', port=8123, username='pipeline', password=pwd, database='tushare'
)

def escape_value(val):
    """Escape a single value for SQL INSERT."""
    if val is None:
        return 'NULL'
    if isinstance(val, date):
        return f"'{val.isoformat()}'"
    if isinstance(val, str):
        escaped = val.replace("'", "''").replace('\\', '\\\\')
        return f"'{escaped}'"
    if isinstance(val, (int, float)):
        return str(val)
    return f"'{str(val)}'"

def migrate_table(pg_table, ch_table, ch_database='tushare'):
    cur = pg_conn.cursor()

    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name NOT IN ('created_at', 'updated_at')
        ORDER BY ordinal_position
    """, (pg_table,))
    cols = [r[0] for r in cur.fetchall()]

    col_list = ', '.join(f'`{c}`' for c in cols) + ', `_version`'

    cur.execute(f"SELECT {', '.join(cols)} FROM {pg_table}")
    rows = cur.fetchall()

    version = int(time.time() * 1000)

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        values_parts = []
        for row in batch:
            vals = [escape_value(v) for v in row] + [str(version)]
            values_parts.append(f"({', '.join(vals)})")

        values_clause = ', '.join(values_parts)
        sql = f"INSERT INTO {ch_database}.{ch_table} ({col_list}) VALUES {values_clause}"
        ch_client.command(sql)
        print(f"  {min(i+batch_size, len(rows))}/{len(rows)}")

    print(f"[DONE] {pg_table}: {len(rows):,} rows")

migrate_table('tushare_stock_company', 'tushare_stock_company')
migrate_table('tushare_index_basic', 'tushare_index_basic')

pg_conn.close()
ch_client.close()
print("All done!")
