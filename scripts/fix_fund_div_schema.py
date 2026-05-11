"""Fix fund_div table schema - remove DoubleDelta codec from String columns."""
import os
import clickhouse_connect

def get_client():
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
    )

def main():
    client = get_client()

    # Drop shadow/old tables
    client.command("DROP TABLE IF EXISTS tushare.tushare_fund_div_shadow")
    client.command("DROP TABLE IF EXISTS tushare.tushare_fund_div_old")

    # Create new table without DoubleDelta on String columns
    create_sql = (
        "CREATE TABLE tushare.tushare_fund_div_shadow ("
        "`ts_code` LowCardinality(String), "
        "`ann_date` Date, "
        "`imp_anndate` Date, "
        "`base_date` Date, "
        "`div_proc` String, "
        "`record_date` Date, "
        "`ex_date` Date, "
        "`pay_date` Date, "
        "`earpay_date` Nullable(String), "
        "`net_ex_date` Date, "
        "`div_cash` Float64, "
        "`base_unit` Float64, "
        "`ear_distr` Float64, "
        "`ear_amount` Decimal(18, 2), "
        "`account_date` Nullable(String), "
        "`base_year` Date, "
        "`_version` UInt64"
        ") ENGINE = ReplacingMergeTree(_version) "
        "PARTITION BY toYYYYMM(ann_date) "
        "ORDER BY (ts_code, ann_date) "
        "SETTINGS index_granularity = 8192"
    )

    print("Creating shadow table...")
    client.command(create_sql)
    print("Shadow table created")

    # Rename atomically
    print("Renaming tables...")
    client.command(
        "RENAME TABLE "
        "tushare.tushare_fund_div TO tushare.tushare_fund_div_old, "
        "tushare.tushare_fund_div_shadow TO tushare.tushare_fund_div"
    )

    # Drop old
    client.command("DROP TABLE IF EXISTS tushare.tushare_fund_div_old")
    print("Old table dropped")

    # Verify
    result = client.query(
        "SELECT sorting_key FROM system.tables "
        "WHERE database = 'tushare' AND name = 'tushare_fund_div'"
    )
    print("New ORDER BY: " + str(result.result_rows[0][0]))

    # Test insert
    from tushare_db.config.loader import load_interface_specs
    from tushare_db.core.tushare_client import TushareClient
    from tushare_db.runner.worker import _normalize_items, _insert_with_evolve
    import json

    with open("/app/data/samples/fund_div.json") as f:
        sample = json.load(f)
    data = sample.get("data", {})
    fields = data.get("fields", [])
    items = data.get("items", [])

    normalized = _normalize_items(fields, items, column_types={})
    print("Normalized " + str(len(normalized)) + " rows")

    _insert_with_evolve(client, "tushare_fund_div", fields, normalized, items)
    count = client.command("SELECT count() FROM tushare.tushare_fund_div")
    print("Table now has " + str(int(count)) + " rows")

    client.close()

if __name__ == "__main__":
    main()
