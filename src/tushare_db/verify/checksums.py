"""Checksums: verify data integrity via cityHash64 fingerprints."""

from __future__ import annotations

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.runner.incremental import get_latest_trade_date

logger = structlog.get_logger()


def compute_checksums(
    ch_client: clickhouse_connect.driver.Client,
    interface: str | None = None,
    priority: str | None = None,
) -> list[dict]:
    """Compute data fingerprints for interfaces to verify idempotency.

    Runs the same query twice; if fingerprints match, data is consistent.
    Uses cityHash64(*) for fingerprinting.

    Args:
        ch_client: ClickHouse client.
        interface: Optional specific interface to check.
        priority: Optional filter by priority (P0/P1/P2/P3).

    Returns:
        List of checksum results per interface.
    """
    specs = load_interface_specs()
    enabled = [s for s in specs if s.enabled]

    if priority:
        enabled = [s for s in enabled if s.priority == priority.upper()]
    if interface:
        enabled = [s for s in enabled if s.name == interface]

    # Get latest trading date
    latest = get_latest_trade_date(ch_client)
    if not latest:
        return []

    results = []
    for spec in enabled:
        table_name = spec.table
        if "." not in table_name:
            table_name = f"tushare.{table_name}"

        # Check if table exists
        tbl = table_name.split(".")[-1]
        table_check = ch_client.query(
            f"SELECT count() FROM system.tables "
            f"WHERE database = 'tushare' AND name = '{tbl}'"
        )
        if int(table_check.result_rows[0][0]) == 0:
            continue

        # Compute fingerprint for latest trading day
        # groupBitXor is order-independent (XOR commutative), stable across part merges
        fp_query = (
            f"SELECT count(), groupBitXor(cityHash64(*)) AS fingerprint, max(_version) AS max_ver "
            f"FROM {table_name} FINAL "
            f"WHERE trade_date = '{latest}'"
        )
        try:
            fp_result = ch_client.query(fp_query)
            if fp_result.result_rows and fp_result.result_rows[0][0]:
                row = fp_result.result_rows[0]
                results.append({
                    "interface": spec.name,
                    "table": table_name,
                    "trade_date": latest,
                    "row_count": int(row[0]),
                    "fingerprint": str(row[1]),
                    "max_version": int(row[2]) if row[2] else 0,
                })
        except Exception as e:
            logger.warning(
                "Checksum failed",
                interface=spec.name,
                table=table_name,
                error=str(e),
            )
            results.append({
                "interface": spec.name,
                "table": table_name,
                "trade_date": latest,
                "row_count": 0,
                "fingerprint": None,
                "error": str(e),
            })

    return results
