"""Unit tests: migration version calculation."""

from datetime import datetime
from zoneinfo import ZoneInfo
from tushare_db.migration.version_calc import calc_version, _to_ms


def test_calc_version_uses_updated_at():
    row = {
        "updated_at": datetime(2024, 6, 1, 10, 30, 0),
        "created_at": datetime(2024, 5, 1, 10, 30, 0),
    }
    v = calc_version(row)
    assert v > 0
    assert isinstance(v, int)


def test_calc_version_falls_back_to_created():
    row = {"updated_at": None, "created_at": datetime(2024, 5, 1, 10, 30, 0)}
    v = calc_version(row)
    assert v > 0


def test_calc_version_falls_back_to_now():
    row = {"updated_at": None, "created_at": None}
    v = calc_version(row)
    assert v > 1700000000000


def test_to_ms_naive_datetime():
    dt = datetime(2024, 6, 1, 10, 30, 0)
    ms = _to_ms(dt)
    assert isinstance(ms, int)
    assert ms > 0


def test_to_ms_aware_datetime():
    tz = ZoneInfo("Asia/Shanghai")
    dt = datetime(2024, 6, 1, 10, 30, 0, tzinfo=tz)
    ms = _to_ms(dt)
    assert isinstance(ms, int)
