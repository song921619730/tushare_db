"""Work unit data structures and helpers."""

from __future__ import annotations

from dataclasses import dataclass

from tushare_db.config.models import InterfaceSpec


@dataclass
class UnitState:
    """Runtime state for a work unit."""

    status: str = "pending"  # pending/running/done/partial/failed/biz_err
    rows: int = 0
    attempts: int = 0
    last_error: str = ""


@dataclass
class SyncRun:
    """State for an entire sync run."""

    run_id: str = ""
    interface: str = ""
    batch: str = ""
    units_total: int = 0
    units_done: int = 0
    units_failed: int = 0
    status: str = "running"
