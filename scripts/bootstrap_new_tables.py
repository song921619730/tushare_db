"""Bootstrap all newly discovered PG tables in ClickHouse."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import clickhouse_connect
import psycopg

CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "pipeline"
CH_PASSWORD = "wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E"

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "market_user"
PG_PASSWORD = "market_password"
PG_DB = "market_db"


def get_pg_columns(pg_conn, table_name):
    """Get column names and types from PG table."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, numeric_precision, numeric_scale,
               character_maximum_length, udt_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return cur.fetchall()


def pg_to_ch_type(col_info):
    """Convert PG type to CH type."""
    col_name, data_type, num_prec, num_scale, char_max, udt_name = col_info

    if data_type == "character varying" or data_type == "text" or data_type == "character":
        return "String"
    elif data_type == "integer" or data_type == "smallint":
        return "Int32"
    elif data_type == "bigint":
        return "Int64"
    elif data_type == "numeric" or data_type == "decimal":
        prec = num_prec or 18
        scale = num_scale or 2
        return f"Decimal({prec}, {scale})"
    elif data_type == "double precision":
        return "Float64"
    elif data_type == "real":
        return "Float32"
    elif data_type == "date":
        return "Date"
    elif data_type == "timestamp without time zone" or data_type == "timestamp with time zone":
        return "DateTime"
    elif data_type == "boolean":
        return "UInt8"
    else:
        return "String"


def bootstrap_table(ch_client, pg_conn, table_name):
    """Create CH table from PG schema."""
    cols = get_pg_columns(pg_conn, table_name)

    # Filter out created_at, updated_at
    cols = [c for c in cols if c[0] not in ("created_at", "updated_at")]

    ch_cols = []
    for col_info in cols:
        col_name = col_info[0]
        ch_type = pg_to_ch_type(col_info)
        # Make String columns Nullable to handle NULLs
        if ch_type == "String":
            ch_type = "Nullable(String)"
        elif ch_type.startswith("Decimal"):
            ch_type = f"Nullable({ch_type})"
        elif ch_type in ("Float32", "Float64", "Int32", "Int64", "Date", "DateTime"):
            ch_type = f"Nullable({ch_type})"
        ch_cols.append(f"    `{col_name}` {ch_type}")

    # Add _version
    ch_cols.append("    `_version` UInt64")

    # Find date column for ORDER BY
    date_cols = [c[0] for c in cols if "date" in c[0].lower()]
    if "ts_code" in [c[0] for c in cols]:
        order_parts = ["ts_code"]
        if date_cols:
            order_parts.append(date_cols[0])
        order_by = ", ".join(order_parts)
    elif date_cols:
        order_by = date_cols[0]
    else:
        order_by = cols[0][0] if cols else "1"

    create_sql = f"""CREATE TABLE IF NOT EXISTS tushare.{table_name}
(
{",\n".join(ch_cols)}
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY ({order_by})
SETTINGS index_granularity = 8192"""

    try:
        ch_client.command(create_sql)
        print(f"  OK: {table_name}")
    except Exception as e:
        print(f"  FAIL: {table_name}: {e}")


def main():
    ch_client = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER,
        password=CH_PASSWORD, database="tushare"
    )
    pg_conn = psycopg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=PG_PASSWORD, dbname=PG_DB
    )

    tables = [
        "tushare_stk_factor_pro", "tushare_index_weight", "tushare_margin_detail",
        "tushare_stock_monthly", "tushare_cyq_perf", "tushare_dc_daily",
        "tushare_fund_daily", "tushare_fx_daily", "tushare_fund_basic",
        "tushare_index_basic", "tushare_stock_company", "tushare_opt_basic",
        "tushare_fut_basic", "tushare_shibor", "tushare_fut_daily",
        "tushare_sge_daily", "tushare_cb_basic", "tushare_cn_m",
        "tushare_cn_cpi", "tushare_cn_ppi", "tushare_cn_gdp",
        "tushare_etf_basic", "tushare_hibor", "tushare_libor",
        "tushare_sge_basic", "tushare_shibor_lpr", "tushare_fx_obasic",
        "tushare_index_daily",
    ]

    print(f"Bootstrapping {len(tables)} tables...")
    for t in tables:
        bootstrap_table(ch_client, pg_conn, t)

    pg_conn.close()
    ch_client.close()
    print("Done!")


if __name__ == "__main__":
    main()
