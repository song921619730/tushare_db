"""Version calculation: compute _version (ms timestamp) from PG row metadata."""

from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")


def calc_version(row: dict) -> int:
    """Compute _version (ms timestamp) from row's updated_at / created_at.

    Priority:
      1. row['updated_at'] if not None
      2. row['created_at'] if not None
      3. current time
    """
    for col in ("updated_at", "created_at"):
        v = row.get(col)
        if v is not None:
            return _to_ms(v)
    return int(time.time() * 1000)


def _to_ms(dt: datetime) -> int:
    """Convert (possibly naive) datetime to Asia/Shanghai ms timestamp."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_TZ_SHANGHAI)
    return int(dt.timestamp() * 1000)


def verify_timezone_assumption(conn, sample_table: str = "tushare_stock_daily") -> bool:
    """Check PG timestamps look reasonable (not UTC vs local issue).

    We compare updated_at against now() — if updated_at is within a few days
    of now, PG stores local time. If it's ~8 hours behind, it's UTC.
    Note: trade_date is the data date, NOT the row update time, so we can't
    use it to verify timezone.
    """
    from datetime import datetime, timedelta
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT updated_at FROM {sample_table}
            WHERE updated_at IS NOT NULL
            ORDER BY updated_at DESC LIMIT 10
        """)
        rows = cur.fetchall()
        if not rows:
            return True
        latest = rows[0][0]
        now = datetime.utcnow()
        delta = abs(now - latest.replace(tzinfo=None))
        # If latest update is within ~7 days, PG is local time. OK.
        # If it's 8+ hours behind (but still recent), it's UTC.
        if delta > timedelta(days=30):
            print(f"[WARN] Latest PG updated_at ({latest}) is {delta} behind now ({now})")
            return False
        # Check if ~8 hours offset (UTC)
        hours_diff = abs(delta.total_seconds() / 3600)
        if 7 < hours_diff < 9:
            print(f"[WARN] PG timestamps appear to be UTC (~{hours_diff:.1f}h offset)")
            return False
    return True
