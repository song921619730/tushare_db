"""Gap detector: find missing trading days and financial periods."""

from __future__ import annotations

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.config.models import InterfaceSpec

logger = structlog.get_logger()

# Standard quarterly period end dates for financial reports
_QUARTER_ENDS = [
    ("0331", "Q1"),
    ("0630", "Q2"),
    ("0930", "Q3"),
    ("1231", "Q4"),
]


def detect_gaps(
    ch_client: clickhouse_connect.driver.Client,
    interface: str | None = None,
    max_gap_days: int = 10,
) -> list[dict]:
    """Detect missing trading days and financial periods.

    For date_loop interfaces: finds dates in trade_cal absent from data.
    For period_loop interfaces: finds missing quarterly periods.

    Args:
        ch_client: ClickHouse client.
        interface: Optional specific interface to check.
        max_gap_days: Maximum gap size to report (smaller gaps = noise).

    Returns:
        List of gap reports per interface.
    """
    specs = load_interface_specs()
    enabled = [s for s in specs if s.enabled]
    if interface is not None:
        enabled = [s for s in enabled if s.name == interface]

    results: list[dict] = []

    # Date-loop gap detection (trading days)
    date_loop_specs = [
        s for s in enabled
        if s.fetch_strategy.kind in ("date_loop", "offset_paging")
    ]
    results.extend(_detect_date_gaps(ch_client, date_loop_specs, max_gap_days))

    # Period-loop gap detection (financial quarters)
    period_loop_specs = [
        s for s in enabled
        if s.fetch_strategy.kind == "period_loop"
    ]
    results.extend(_detect_period_gaps(ch_client, period_loop_specs))

    return results


def _detect_date_gaps(
    ch_client: clickhouse_connect.driver.Client,
    specs: list[InterfaceSpec],
    max_gap_days: int,
) -> list[dict]:
    """Detect missing trading days for date_loop interfaces."""
    if not specs:
        return []

    cal_result = ch_client.query(
        "SELECT min(cal_date), max(cal_date) FROM _meta.trade_cal "
        "WHERE is_open = 1"
    )
    if not cal_result.result_rows or not cal_result.result_rows[0][0]:
        return []

    min_date, max_date = cal_result.result_rows[0]
    if hasattr(min_date, "strftime"):
        min_date_str = min_date.strftime("%Y%m%d")
        max_date_str = max_date.strftime("%Y%m%d")
    else:
        min_date_str = str(min_date).replace("-", "")[:8]
        max_date_str = str(max_date).replace("-", "")[:8]

    results = []
    for spec in specs:
        table_name = spec.table
        if "." not in table_name:
            table_name = f"tushare.{table_name}"

        tbl = table_name.split(".")[-1]
        table_check = ch_client.query(
            f"SELECT count() FROM system.tables "
            f"WHERE database = 'tushare' AND name = '{tbl}'"
        )
        if int(table_check.result_rows[0][0]) == 0:
            continue

        gap_query = (
            f"SELECT cal_date FROM _meta.trade_cal "
            f"WHERE is_open = 1 AND cal_date >= '{min_date_str}' AND cal_date <= '{max_date_str}' "
            f"AND cal_date NOT IN ("
            f"  SELECT DISTINCT trade_date FROM {table_name} "
            f"  WHERE trade_date >= '{min_date_str}' AND trade_date <= '{max_date_str}'"
            f") ORDER BY cal_date"
        )
        gap_result = ch_client.query(gap_query)
        missing_dates = []
        for row in gap_result.result_rows:
            dt = row[0]
            if hasattr(dt, "strftime"):
                missing_dates.append(dt.strftime("%Y%m%d"))
            else:
                missing_dates.append(str(dt).replace("-", "")[:8])

        if missing_dates:
            results.append({
                "interface": spec.name,
                "table": table_name,
                "gap_type": "trading_day",
                "missing_dates": missing_dates,
                "missing_count": len(missing_dates),
                "date_range": f"{min_date_str}..{max_date_str}",
            })

    return results


def _detect_period_gaps(
    ch_client: clickhouse_connect.driver.Client,
    specs: list[InterfaceSpec],
) -> list[dict]:
    """Detect missing quarterly periods for financial (period_loop) interfaces."""
    results = []
    for spec in specs:
        table_name = spec.table
        if "." not in table_name:
            table_name = f"tushare.{table_name}"

        tbl = table_name.split(".")[-1]
        table_check = ch_client.query(
            f"SELECT count() FROM system.tables "
            f"WHERE database = 'tushare' AND name = '{tbl}'"
        )
        if int(table_check.result_rows[0][0]) == 0:
            continue

        # Determine date field (period or ann_date)
        date_field = "period"
        if spec.fetch_strategy.date_field:
            date_field = spec.fetch_strategy.date_field

        # Get actual periods present in the table
        period_result = ch_client.query(
            f"SELECT DISTINCT {date_field} FROM {table_name} FINAL "
            f"WHERE {date_field} IS NOT NULL ORDER BY {date_field}"
        )
        actual_periods = {str(r[0]).replace("-", "")[:8] for r in period_result.result_rows if r[0]}

        if not actual_periods:
            results.append({
                "interface": spec.name,
                "table": table_name,
                "gap_type": "financial_period",
                "missing_count": 0,
                "missing_periods": [],
                "date_range": "empty",
                "issue": "Table has no data",
            })
            continue

        # Compute expected periods from min to max year (inclusive of full max year)
        min_period = min(actual_periods)
        max_period = max(actual_periods)
        min_year = int(min_period[:4])
        max_year = int(max_period[:4])

        # Generate all quarterly periods from min_year to max_year (full years)
        expected = set()
        for year in range(min_year, max_year + 1):
            for suffix, _qname in _QUARTER_ENDS:
                expected.add(f"{year}{suffix}")

        missing = sorted(expected - actual_periods)

        if missing:
            results.append({
                "interface": spec.name,
                "table": table_name,
                "gap_type": "financial_period",
                "missing_periods": missing,
                "missing_count": len(missing),
                "date_range": f"{min_period}..{max_period}",
            })

    return results
