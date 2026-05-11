"""Injectable clock for testability."""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo
from typing import Protocol

import pytz


class Clock(Protocol):
    """Interface for time sources."""

    def now(self, tz: tzinfo | None = None) -> datetime: ...


class SystemClock:
    """Real system clock."""

    def now(self, tz: tzinfo | None = None) -> datetime:
        return datetime.now(tz)


class FakeClock:
    """Injectable fake clock for tests."""

    def __init__(self, fixed: datetime | None = None) -> None:
        self._fixed = fixed or datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai"))
        self._offset_seconds: float = 0

    def now(self, tz: tzinfo | None = None) -> datetime:
        result = self._fixed
        if self._offset_seconds:
            from datetime import timedelta
            result = result + timedelta(seconds=self._offset_seconds)
        return result if tz is None else result.astimezone(tz)

    def advance(self, seconds: float) -> None:
        self._offset_seconds += seconds

    def set(self, dt: datetime) -> None:
        self._fixed = dt
        self._offset_seconds = 0
