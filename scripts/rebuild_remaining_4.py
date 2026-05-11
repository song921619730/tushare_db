"""Rebuild 4 tables with corrected ORDER BY."""
import os
import clickhouse_connect


TABLES = [
    ("tushare_stk_managers", "ts_code, ann_date"),
    ("tushare_kpl_concept_cons", "ts_code, con_code, trade_date"),
    ("tushare_tdx_member", "ts_code, con_code, trade_date"),
]


def get_client():
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="tushare",
        connect_timeout=10,
        send_receive_timeout=300,
    )


def rebuild(client, table, order_by):
    print(f"\n--- {table} ---")
    exists = client.command(
        f"SELECT count() FROM system.tables WHERE database='tushare' AND name='{table}'"
    )
    if int(exists) == 0:
        print(f"  SKIP: table does not exist")
        return False

    count = client.command(f"SELECT count() FROM tushare.{table}")
    print(f"  Current rows: {count}")
    print(f"  New ORDER BY: ({order_by})")

    ddl = client.command(f"SHOW CREATE TABLE tushare.{table}")
    # Normalize escaped newlines to actual newlines
    bs = chr(92)  # backslash
    ddl = ddl.replace(bs + "n", "\n")
    shadow = f"{table}_rebuild"
    old = f"{table}_old"

    client.command(f"DROP TABLE IF EXISTS tushare.{shadow}")
    client.command(f"DROP TABLE IF EXISTS tushare.{old}")

    # Create shadow with correct ORDER BY
    create_sql = ddl.replace(f"CREATE TABLE tushare.{table}", f"CREATE TABLE tushare.{shadow}", 1)
    # Replace ORDER BY line
    lines = ddl.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('ORDER BY') and 'tuple()' not in stripped:
            new_lines.append(f'ORDER BY ({order_by})')
        else:
            new_lines.append(line)
    create_sql = '\n'.join(new_lines)
    print(f"  Creating shadow...")
    client.command(create_sql)

    if int(count) > 0:
        print(f"  Copying data...")
        client.command(f"INSERT INTO {shadow} SELECT * FROM {table}")

    new_count = client.command(f"SELECT count() FROM tushare.{shadow}")
    print(f"  Shadow rows: {new_count}")

    print(f"  Renaming...")
    client.command(f"RENAME TABLE {table} TO {old}, {shadow} TO {table}")
    client.command(f"DROP TABLE IF EXISTS {old}")

    sorting = client.command(
        f"SELECT sorting_key FROM system.tables WHERE database='tushare' AND name='{table}'"
    )
    print(f"  Verified ORDER BY: {sorting}")
    return True


def main():
    client = get_client()
    for table, order_by in TABLES:
        try:
            rebuild(client, table, order_by)
        except Exception as e:
            print(f"  ERROR: {e}")

    # Reset sync state for these interfaces
    print("\n--- Resetting sync_state ---")
    for table, _ in TABLES:
        iface = table.replace("tushare_", "")
        try:
            client.command(f"ALTER TABLE _meta.sync_state DELETE WHERE interface='{iface}'")
            print(f"  Deleted sync for {iface}")
        except Exception as e:
            print(f"  WARN {iface}: {e}")

    print("\nDone. Run backfill to repopulate.")


if __name__ == "__main__":
    main()
