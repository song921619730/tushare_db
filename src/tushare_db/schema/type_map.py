"""Type mapping: Python values -> ClickHouse column types with normalization rules.

Normalization rules (design doc §4):
- Financial fields (*_amount/*_revenue/*_profit): Tushare 万元 -> ClickHouse Decimal64(2) 元
- Fund shares (*_share/*_amount): 万份 -> 份
- Date: String("YYYYMMDD") -> Date; String("YYYY-MM-DD HH:MM:SS") -> DateTime
- Percentage: keep original (1.23 means 1.23%, no ÷100)
"""

from __future__ import annotations

import re
from typing import Any

# Patterns for type inference
_DATE_YYYYMMDD = re.compile(r"^\d{8}$")
_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?$")

# Financial field suffixes that need 万元 -> 元 conversion
_FINANCIAL_AMOUNT_SUFFIXES = (
    "_amount", "_revenue", "_profit", "_cost", "_income",
    "_expense", "_asset", "_liability", "_equity",
    "_mv",  # market value: total_mv, circ_mv
)

# total_* fields that ARE amounts (should be normalized)
_AMOUNT_TOTAL_WHITELIST = {
    "total_revenue", "total_profit", "total_cogs", "total_assets",
    "total_liab", "total_hldr_eqy", "total_hldr_eqy_exc_min_int",
    "total_mv", "total_cur_assets", "total_nca", "total_cur_liab",
    "total_ncl", "total_oper_revenue", "total_oper_cost",
    "total_non_current_asset", "total_current_asset",
    "total_current_liab", "total_non_current_liab",
}

# total_* fields that are NOT amounts (must NOT be normalized)
_AMOUNT_TOTAL_BLACKLIST = {
    "total_share", "total_holders", "holder_total",
    "total_holder", "total_shares",
}

# Fund share fields
_FUND_SHARE_SUFFIXES = ("_share", "_amount")

# LowCardinality candidates (low cardinality string fields)
_LOW_CARDINALITY_FIELDS = {"ts_code", "exchange", "market", "area", "industry", "name"}


def infer_ch_type(field_name: str, sample_values: list[Any]) -> str:
    """Infer ClickHouse column type from field name and sample values.

    Args:
        field_name: Column name from Tushare API.
        sample_values: List of sample values from API response.

    Returns:
        ClickHouse type string (e.g., 'Date', 'Float64', 'Decimal64(2)').
    """
    # Check for known low-cardinality fields
    if field_name in _LOW_CARDINALITY_FIELDS:
        return "LowCardinality(String)"

    # Apply normalization overrides based on field name
    if _needs_financial_normalization(field_name):
        return "Decimal64(2)"

    if _needs_fund_share_normalization(field_name):
        return "Decimal64(4)"

    # Infer from sample values
    non_null = [v for v in sample_values if v is not None and v != ""]
    if not non_null:
        return "String"  # Fallback

    sample = non_null[0]

    # Date detection
    if isinstance(sample, str):
        if _DATE_YYYYMMDD.match(sample):
            return "Date"
        if _DATE_ISO.match(sample):
            if len(sample) > 10:
                return "DateTime"
            return "Date"

    # Numeric detection
    if isinstance(sample, (int, float)):
        if isinstance(sample, float) or any(isinstance(v, float) for v in non_null[:10]):
            return "Float64"
        return "Int64"

    # String fallback
    return "String"


def _needs_financial_normalization(field_name: str) -> bool:
    """Check if field needs 万元 -> 元 conversion."""
    lower = field_name.lower()

    if lower in _AMOUNT_TOTAL_BLACKLIST:
        return False
    if any(lower.endswith(suf) for suf in _FINANCIAL_AMOUNT_SUFFIXES):
        return True
    # total_xxx — only if explicitly whitelisted
    if lower.startswith("total_") and lower in _AMOUNT_TOTAL_WHITELIST:
        return True
    return False


def _needs_fund_share_normalization(field_name: str) -> bool:
    """Check if field needs 万份 -> 份 conversion."""
    lower = field_name.lower()
    return any(lower.endswith(suf) for suf in _FUND_SHARE_SUFFIXES)


def normalize_value(field_name: str, ch_type: str, value: Any) -> Any:
    """Normalize a value before writing to ClickHouse.

    Args:
        field_name: Column name.
        ch_type: Target ClickHouse type.
        value: Raw value from Tushare API.

    Returns:
        Normalized value.
    """
    if value is None or value == "":
        return None

    # Financial fields: convert 万元 to 元 (multiply by 10000)
    if ch_type == "Decimal64(2)" and _needs_financial_normalization(field_name):
        try:
            return float(value) * 10000
        except (ValueError, TypeError):
            return value

    # Fund shares: convert 万份 to 份
    if ch_type == "Decimal64(4)" and _needs_fund_share_normalization(field_name):
        try:
            return float(value) * 10000
        except (ValueError, TypeError):
            return value

    return value
