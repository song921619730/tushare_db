#!/usr/bin/env python3
"""Verify sync_state cleanup after running clear_stale_sync_state.sql.

Usage:
    python scripts/verify_cleanup.py [--host HOST] [--port PORT] [--password PASSWORD]

Connects to ClickHouse and reports:
  - Remaining running/failed sync_state records
  - Total record count per interface
  - Summary of cleanup effectiveness
"""

import argparse
import sys

try:
    import clickhouse_connect
except ImportError:
    print("ERROR: clickhouse_connect package not installed.", file=sys.stderr)
    print("Install with: pip install clickhouse-connect", file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Verify sync_state cleanup")
    parser.add_argument("--host", default="localhost", help="ClickHouse host (default: localhost)")
    parser.add_argument("--port", type=int, default=8123, help="ClickHouse HTTP port (default: 8123)")
    parser.add_argument("--user", default="default", help="ClickHouse user (default: default)")
    parser.add_argument("--password", default="", help="ClickHouse password")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"Connecting to ClickHouse at {args.host}:{args.port}...")

    try:
        client = clickhouse_connect.get_client(
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
        )
        # Verify connection
        version = client.server_version
        print(f"Connected. Server version: {version}")
    except Exception as e:
        print(f"ERROR: Failed to connect to ClickHouse: {e}", file=sys.stderr)
        sys.exit(1)

    # Query 1: Interface + status breakdown
    print("\n" + "=" * 70)
    print("SYNC STATE BY INTERFACE AND STATUS")
    print("=" * 70)

    result = client.query(
        """
        SELECT interface, status, count() AS cnt
        FROM _meta.sync_state
        GROUP BY interface, status
        ORDER BY interface, status
        """
    )

    if not result.result_rows:
        print("  (no records found)")
    else:
        current_interface = None
        for interface, status, cnt in result.result_rows:
            if interface != current_interface:
                print(f"\n  {interface}:")
                current_interface = interface
            print(f"    {status}: {cnt:,}")

    # Query 2: Remaining running/failed records (the ones we care about)
    print("\n" + "=" * 70)
    print("REMAINING RUNNING/FAILED RECORDS")
    print("=" * 70)

    result = client.query(
        """
        SELECT interface, status, count() AS cnt
        FROM _meta.sync_state
        WHERE status IN ('running', 'failed')
        GROUP BY interface, status
        ORDER BY interface, status
        """
    )

    if not result.result_rows:
        print("  None. All running/failed records have been cleared.")
    else:
        total_bad = 0
        for interface, status, cnt in result.result_rows:
            print(f"  {interface} [{status}]: {cnt:,}")
            total_bad += cnt
        print(f"\n  Total remaining running/failed: {total_bad:,}")

    # Query 3: Total count
    print("\n" + "=" * 70)
    print("TOTAL SYNC STATE RECORDS")
    print("=" * 70)

    result = client.query("SELECT count() FROM _meta.sync_state")
    total = result.result_rows[0][0]
    print(f"  Total records: {total:,}")

    # Query 4: Status summary
    print("\n" + "=" * 70)
    print("STATUS SUMMARY")
    print("=" * 70)

    result = client.query(
        """
        SELECT status, count() AS cnt
        FROM _meta.sync_state
        GROUP BY status
        ORDER BY status
        """
    )

    for status, cnt in result.result_rows:
        pct = (cnt / total * 100) if total > 0 else 0
        print(f"  {status}: {cnt:>10,} ({pct:5.1f}%)")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

    client.close()


if __name__ == "__main__":
    main()
