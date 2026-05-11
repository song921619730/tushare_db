"""Fix fund tables: drop and recreate with proper schema (no DoubleDelta on String)."""
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


TABLES = {
    "tushare_fund_div": {
        "partition_key": "toYYYYMM(ann_date)",
        "order_by": "ts_code, ann_date",
        "columns": [
            ("ts_code", "LowCardinality(String)"),
            ("ann_date", "Date"),
            ("imp_anndate", "Date"),
            ("base_date", "Date"),
            ("div_proc", "String"),
            ("record_date", "Date"),
            ("ex_date", "Date"),
            ("pay_date", "Date"),
            ("earpay_date", "Nullable(String)"),
            ("net_ex_date", "Date"),
            ("div_cash", "Float64"),
            ("base_unit", "Float64"),
            ("ear_distr", "Float64"),
            ("ear_amount", "Decimal(18, 2)"),
            ("account_date", "Nullable(String)"),
            ("base_year", "Date"),
            ("_version", "UInt64"),
        ],
    },
}


def main():
    client = get_client()

    for table_name, info in TABLES.items():
        print("Fixing " + table_name + "...")

        # Drop old tables
        client.command("DROP TABLE IF EXISTS tushare." + table_name + "_old")
        client.command("DROP TABLE IF EXISTS tushare." + table_name + "_shadow")

        # Build CREATE DDL
        col_defs = []
        for col_name, col_type in info["columns"]:
            codec = ""
            if col_type == "Date":
                codec = " CODEC(DoubleDelta, ZSTD(3))"
            col_defs.append("`" + col_name + "` " + col_type + codec)

        create_sql = (
            "CREATE TABLE tushare." + table_name + "_shadow ("
            + ", ".join(col_defs)
            + ") ENGINE = ReplacingMergeTree(_version) "
            + "PARTITION BY " + info["partition_key"] + " "
            + "ORDER BY (" + info["order_by"] + ") "
            + "SETTINGS index_granularity = 8192"
        )

        client.command(create_sql)
        print("  Shadow table created")

        # Atomic rename if original exists
        exists = client.command(
            "SELECT count() FROM system.tables "
            "WHERE database='tushare' AND name='" + table_name + "'"
        )
        if int(exists) > 0:
            client.command(
                "RENAME TABLE "
                "tushare." + table_name + " TO tushare." + table_name + "_old, "
                "tushare." + table_name + "_shadow TO tushare." + table_name
            )
            client.command("DROP TABLE IF EXISTS tushare." + table_name + "_old")
            print("  Old table replaced")
        else:
            client.command(
                "RENAME TABLE tushare." + table_name + "_shadow TO tushare." + table_name
            )
            print("  Created")

        # Verify
        result = client.query(
            "SELECT sorting_key FROM system.tables "
            "WHERE database='tushare' AND name='" + table_name + "'"
        )
        print("  ORDER BY: " + str(result.result_rows[0][0]))

        # Check codecs
        ddl = client.command("SHOW CREATE TABLE tushare." + table_name)
        bs = chr(92)
        ddl = ddl.replace(bs + "n", "\n")
        if "Nullable(String) CODEC" in ddl:
            print("  WARNING: Nullable(String) still has CODEC!")
        else:
            print("  Schema OK - no codec on Nullable(String)")

    client.close()


if __name__ == "__main__":
    main()
