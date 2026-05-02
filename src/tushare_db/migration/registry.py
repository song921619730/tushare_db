"""Registry: load and validate tables.yaml migration specs."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class TableSpec(BaseModel):
    """Single table migration specification."""

    model_config = ConfigDict(extra="forbid")

    pg_table: str
    ch_table: str
    ch_database: str = "tushare"
    priority: Literal["P0", "P1", "P2", "P3", "P4"]
    partitioned: bool = False
    partition_pattern: str | None = None
    partition_years: list[int] = Field(default_factory=list)
    include_default_partition: bool = False
    date_column: str | None = None
    batch_size: int = 100_000
    expected_rows: int | None = None
    column_renames: dict[str, str] = Field(default_factory=dict)
    drop_pg_columns: list[str] = Field(default_factory=list)
    notes: str = ""


def load_tables(path: Path | str = "config/migration/tables.yaml") -> list[TableSpec]:
    """Load migration table specs from YAML."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [TableSpec(**item) for item in raw]


def filter_by_priority(specs: list[TableSpec], priority: str) -> list[TableSpec]:
    """Filter specs by priority level."""
    return [s for s in specs if s.priority == priority]
