"""Pydantic models for interface specifications and configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FetchStrategy(BaseModel):
    """Defines how data is fetched from Tushare."""

    kind: str = Field(
        description="full_once|date_loop|period_loop|monthly_window|per_symbol|per_symbol_period|offset_paging"
    )
    date_field: str | None = Field(default=None, description="trade_date|end_date|cal_date")
    step: int | None = Field(default=None, description="Days per fetch for date_loop")
    symbol_source: str | None = Field(
        default=None, description="Source table for ts_code list (per_symbol_period)"
    )
    static_params: dict[str, str] | None = Field(
        default=None, description="Static params merged into every unit (e.g., freq=W)"
    )


class InterfaceSpec(BaseModel):
    """Single interface declaration from config/interfaces/*.yaml."""

    name: str = Field(description="Tushare API interface name")
    table: str = Field(description="ClickHouse target table name (tushare.*)")
    enabled: bool = Field(default=True, description="Whether this interface is active")
    priority: str = Field(description="P0|P1|P2|P3")
    mode: str = Field(description="full|incremental")
    freq_bucket: str = Field(description="normal|special")
    start_date: str | None = Field(default=None, description="Backfill start YYYYMMDD")
    fetch_strategy: FetchStrategy
    pagination: dict[str, Any] | None = Field(default=None)
    partition_key: str = Field(default="tuple()", description="ClickHouse partition expression")
    order_by: str = Field(description="ClickHouse ORDER BY columns")
    dedupe_key: str | None = Field(default=None, description="Column for deduplication")
    required_params: list[str] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list, description="Explicit field list (empty=auto)")
    schema_overrides: dict[str, Any] = Field(default_factory=dict)
    batch: str = Field(description="A|B|C|D|saturday|reference")

    @property
    def is_per_symbol(self) -> bool:
        return self.fetch_strategy.kind in ("per_symbol", "per_symbol_period")

    @property
    def is_date_loop(self) -> bool:
        return self.fetch_strategy.kind == "date_loop"

    @property
    def is_period_loop(self) -> bool:
        return self.fetch_strategy.kind == "period_loop"
