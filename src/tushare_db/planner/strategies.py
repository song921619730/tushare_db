"""Work unit planning strategies.

Six strategies (design doc §5.2):
- full_once: one-time fetch (e.g., stock_basic:full)
- date_loop: iterate by trading dates (e.g., daily:20240315)
- period_loop: iterate by fiscal quarters (e.g., income:20240331)
- monthly_window: iterate by calendar months (e.g., fund_nav:202403)
- per_symbol_period: iterate by symbol × quarter (saturday long-tail)
- offset_paging: iterate by date + offset (moneyflow family)

Each strategy produces WorkUnit objects with a scope_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class WorkUnit:
    """A single unit of work for one API call."""

    interface: str
    table: str
    scope_key: str
    params: dict
    bucket: str  # "normal" or "special"
    retries: int = 0

    def __repr__(self) -> str:
        return f"WorkUnit({self.interface}, {self.scope_key})"


def build_scope_key(interface: str, strategy: str, **kwargs: str) -> str:
    """Build scope_key according to design doc §5.2 template.

    Templates:
        full_once:            {interface}:full
        date_loop:            {interface}:{trade_date:YYYYMMDD}
        period_loop:          {interface}:{period:YYYYMMDD}
        monthly_window:       {interface}:{ym:YYYYMM}
        per_symbol:           {interface}:{ts_code}
        per_symbol_period:    {interface}:{ts_code}:{period:YYYYMMDD}
        offset_paging:        {interface}:{date}:{offset:08d}
    """
    if strategy == "full_once":
        return f"{interface}:full"
    if strategy == "date_loop":
        return f"{interface}:{kwargs['trade_date']}"
    if strategy == "period_loop":
        return f"{interface}:{kwargs['period']}"
    if strategy == "monthly_window":
        return f"{interface}:{kwargs['ym']}"
    if strategy == "per_symbol":
        return f"{interface}:{kwargs['ts_code']}"
    if strategy == "per_symbol_period":
        return f"{interface}:{kwargs['ts_code']}:{kwargs['period']}"
    if strategy == "offset_paging":
        offset = int(kwargs.get("offset", 0))
        return f"{interface}:{kwargs['date']}:{offset:08d}"
    raise ValueError(f"Unknown strategy: {strategy}")


def generate_full_once_units(
    interface: str,
    bucket: str,
    table: str = "",
) -> list[WorkUnit]:
    """Generate a single work unit for full_once strategy."""
    scope_key = build_scope_key(interface, "full_once")
    return [WorkUnit(interface=interface, table=table, scope_key=scope_key, params={}, bucket=bucket)]


def generate_date_loop_units(
    interface: str,
    bucket: str,
    dates: list[str],
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for each trading date."""
    units = []
    for trade_date in dates:
        scope_key = build_scope_key(interface, "date_loop", trade_date=trade_date)
        units.append(
            WorkUnit(
                interface=interface,
                table=table,
                scope_key=scope_key,
                params={"trade_date": trade_date},
                bucket=bucket,
            )
        )
    return units


def generate_period_loop_units(
    interface: str,
    bucket: str,
    start_date: str = "20200101",
    end_date: str | None = None,
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for fiscal quarters.

    Periods: Q1=0331, Q2=0630, Q3=0930, Q4=1231
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    periods = _generate_quarter_periods(start_date, end_date)
    units = []
    for period in periods:
        scope_key = build_scope_key(interface, "period_loop", period=period)
        units.append(
            WorkUnit(
                interface=interface,
                table=table,
                scope_key=scope_key,
                params={"period": period},
                bucket=bucket,
            )
        )
    return units


def generate_monthly_window_units(
    interface: str,
    bucket: str,
    start_date: str = "20200101",
    end_date: str | None = None,
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for monthly windows."""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    months = _generate_monthly_periods(start_date, end_date)
    units = []
    for ym in months:
        scope_key = build_scope_key(interface, "monthly_window", ym=ym)
        units.append(
            WorkUnit(
                interface=interface,
                table=table,
                scope_key=scope_key,
                params={"month": ym},
                bucket=bucket,
            )
        )
    return units


def generate_per_symbol_units(
    interface: str,
    bucket: str,
    symbols: list[str],
    start_date: str = "20200101",
    end_date: str | None = None,
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for per-symbol fetch (one call per stock, returns all data).

    Used for APIs that don't support period/date filtering — each unit fetches
    the entire history for one symbol.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    units = []
    for symbol in symbols:
        scope_key = build_scope_key(interface, "per_symbol", ts_code=symbol)
        units.append(
            WorkUnit(
                interface=interface,
                table=table,
                scope_key=scope_key,
                params={"ts_code": symbol},
                bucket=bucket,
            )
        )
    return units


def generate_per_symbol_period_units(
    interface: str,
    bucket: str,
    symbols: list[str],
    start_date: str = "20200101",
    end_date: str | None = None,
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for per-symbol × period (saturday long-tail).

    Each unit is one symbol × one quarter.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    periods = _generate_quarter_periods(start_date, end_date)
    units = []
    for symbol in symbols:
        for period in periods:
            scope_key = build_scope_key(
                interface, "per_symbol_period", ts_code=symbol, period=period
            )
            units.append(
                WorkUnit(
                    interface=interface,
                    table=table,
                    scope_key=scope_key,
                    params={"ts_code": symbol, "period": period},
                    bucket=bucket,
                )
            )
    return units


def generate_offset_paging_units(
    interface: str,
    bucket: str,
    dates: list[str],
    page_size: int = 5000,
    table: str = "",
) -> list[WorkUnit]:
    """Generate work units for offset-paginated interfaces (moneyflow family).

    Each unit handles one date with one page of results.
    We generate offset=0 only; the worker handles pagination internally.
    """
    units = []
    for date in dates:
        scope_key = build_scope_key(interface, "offset_paging", date=date, offset="0")
        units.append(
            WorkUnit(
                interface=interface,
                table=table,
                scope_key=scope_key,
                params={"trade_date": date, "offset": 0, "limit": page_size},
                bucket=bucket,
            )
        )
    return units


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_quarter_periods(start_date: str, end_date: str) -> list[str]:
    """Generate quarter-end dates between start and end."""
    quarter_ends = ["0331", "0630", "0930", "1231"]
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])

    periods = []
    for year in range(start_year, end_year + 1):
        for qe in quarter_ends:
            period = f"{year}{qe}"
            if period >= start_date and period <= end_date:
                periods.append(period)
    return periods


def _generate_monthly_periods(start_date: str, end_date: str) -> list[str]:
    """Generate YYYYMM months between start and end."""
    start_year, start_month = int(start_date[:4]), int(start_date[4:6])
    end_year, end_month = int(end_date[:4]), int(end_date[4:6])

    months = []
    year, month = start_year, start_month
    while year < end_year or (year == end_year and month <= end_month):
        months.append(f"{year:04d}{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months
