"""Field resolver: column alignment + unit normalization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

# Columns to always drop from PG
_FORCE_DROP_COLUMNS = {"created_at", "updated_at"}

# Amount/share patterns requiring ×10000 conversion (万元/万份 → 元/份)
_NORMALIZE_X10000_PATTERNS = [
    "amount", "revenue", "profit", "income", "cost",
    "expense", "asset", "liability", "liab", "equity",
    "mv", "capital", "surplus", "tax",
    "ebit", "ebitda", "fcff", "fcfe", "interest", "debt",
    "dividend",
]

# Exclude suffixes (even if pattern matches)
_EXCLUDE_SUFFIXES = (
    "_pct", "_rate", "_ratio", "_price", "_days",
    "_yoy", "_qoq", "_cost_ratio", "_tax_rate",
    "_per_share", "_share_pct",
)
_EXCLUDE_FULL_NAMES = {
    "vol", "amount_vol",
    "turnover_rate",
    "pe", "pe_ttm", "pb", "ps", "ps_ttm",
}


def resolve_columns(
    pg_cols: list[str],
    ch_cols: list[str],
    renames: dict[str, str] | None = None,
    drop_pg_cols: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return (pg_in, ch_in), aligned and same length.

    Steps:
      1. Filter out force-dropped columns (created_at/updated_at + drop_pg_cols)
      2. Map PG columns via renames to CH names
      3. Take intersection with CH columns
    """
    renames = renames or {}
    drop_set = _FORCE_DROP_COLUMNS | set(drop_pg_cols or [])

    pg_clean = [c for c in pg_cols if c not in drop_set]
    ch_set = set(ch_cols)

    pg_in: list[str] = []
    ch_in: list[str] = []
    for pg_col in pg_clean:
        ch_col = renames.get(pg_col, pg_col)
        if ch_col in ch_set:
            pg_in.append(pg_col)
            ch_in.append(ch_col)

    return pg_in, ch_in


def should_normalize(column_name: str, table_name: str = "") -> bool:
    """Check if a column needs ×10000 conversion."""
    col = column_name.lower()
    if col in _EXCLUDE_FULL_NAMES:
        return False
    if col.endswith(_EXCLUDE_SUFFIXES):
        return False
    # *_vol = volume, not amount
    if col == "vol" or col.endswith("_vol"):
        return False
    for pat in _NORMALIZE_X10000_PATTERNS:
        if pat in col:
            return True
    return False


def normalize_value(column_name: str, value: Any, table_name: str = "") -> Any:
    """Apply ×10000 conversion for amount/share fields."""
    if value is None:
        return None
    # Handle NaN and Inf from PG float/numeric columns
    if isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf')):
        return None
    if isinstance(value, Decimal) and (value.is_nan() or value.is_infinite()):
        return None
    if not should_normalize(column_name, table_name):
        return value
    if isinstance(value, (int, float)):
        return value * 10_000
    if isinstance(value, Decimal):
        return float(value) * 10_000
    return value


def normalize_row(
    row: tuple, columns: list[str], table_name: str = ""
) -> tuple:
    """Apply normalize_value to an entire row."""
    return tuple(
        normalize_value(col, val, table_name)
        for col, val in zip(columns, row)
    )


def diff_fields(
    pg_cols: list[str], ch_cols: list[str], renames: dict
) -> dict:
    """Generate pg_only / ch_only / both field diff report."""
    drop_set = _FORCE_DROP_COLUMNS
    pg_clean = set(c for c in pg_cols if c not in drop_set)
    pg_renamed = {renames.get(c, c) for c in pg_clean}
    ch_set = set(ch_cols)

    return {
        "both": sorted(pg_renamed & ch_set),
        "pg_only_drop": sorted(pg_renamed - ch_set),
        "ch_only_default": sorted(ch_set - pg_renamed),
    }
