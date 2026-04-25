"""Backfill orchestrator: select interfaces by layer/priority, plan units, execute."""

from __future__ import annotations

import uuid
from typing import Iterable

import clickhouse_connect.driver
import structlog

from tushare_db.config.loader import load_interface_specs
from tushare_db.config.models import InterfaceSpec
from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.planner import plan_units
from tushare_db.runner.executor import execute_batch

logger = structlog.get_logger()


def get_layer(spec: InterfaceSpec) -> int:
    """Map an InterfaceSpec to its backfill layer (0-5)."""
    batch = spec.batch
    priority = spec.priority
    strategy = spec.fetch_strategy.kind

    # Layer 0: reference tables
    if batch == "reference":
        return 0
    # Layer 1: daily quotes (P0 date_loop interfaces)
    if priority == "P0" and strategy in ("date_loop", "offset_paging"):
        return 1
    # Layer 2: moneyflow & reference (P1 non-period)
    if priority == "P1" and strategy not in ("period_loop", "per_symbol_period"):
        return 2
    # Layer 3: financial period_loop + per_symbol_period long-tail
    if strategy in ("period_loop", "per_symbol_period"):
        return 3
    # Layer 4: concept boards / features (P2)
    if priority == "P2":
        return 4
    # Layer 5: macro / forex / spot (P3)
    return 5


def select_specs(
    layer: int | None = None,
    priority: str | None = None,
    interface: str | None = None,
    backfill_all: bool = False,
) -> list[InterfaceSpec]:
    """Select interface specs for backfill based on filter criteria."""
    specs = load_interface_specs()

    if interface:
        return [s for s in specs if s.name == interface]
    if layer is not None:
        return [s for s in specs if s.enabled and get_layer(s) == layer]
    if priority:
        return [s for s in specs if s.enabled and s.priority == priority]
    if backfill_all:
        return [s for s in specs if s.enabled]
    # Default: P0 + P1
    return [s for s in specs if s.enabled and s.priority in ("P0", "P1")]


def run_backfill(
    specs: Iterable[InterfaceSpec],
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Execute backfill for given specs. Returns summary dict."""
    run_id = uuid.uuid4()
    total_units = 0
    total_done = 0
    total_failed = 0

    for spec in specs:
        units = plan_units(spec, ch_client, start_date=start_date, end_date=end_date)
        if not units:
            logger.info("No units to backfill", interface=spec.name)
            continue

        logger.info("Backfilling interface", interface=spec.name, units=len(units))
        _, done_count, failed_count = execute_batch(
            units, tushare_client, ch_client, run_id=run_id,
        )
        total_units += len(units)
        total_done += done_count
        total_failed += failed_count

    return {
        "run_id": str(run_id),
        "total": total_units,
        "done": total_done,
        "failed": total_failed,
    }
