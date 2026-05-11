"""Type mapping: PostgreSQL data type → ClickHouse type."""

from __future__ import annotations

_LOW_CARDINALITY_FIELDS = {
    "ts_code", "exchange", "market", "area", "industry",
    "list_status", "is_hs", "curr_type",
}


def pg_type_to_ch(pg_type: str, col_name: str) -> str:
    """Convert PostgreSQL data type to ClickHouse type string.

    Args:
        pg_type: Lowercase PG type name (e.g. 'character varying', 'numeric').
        col_name: Column name for low-cardinality heuristics.
    """
    pg_type = pg_type.lower().strip()
    col_lower = col_name.lower()

    # String / VARCHAR / TEXT
    if pg_type in ("character varying", "varchar", "text", "char", "character"):
        if col_lower in _LOW_CARDINALITY_FIELDS:
            return "LowCardinality(String)"
        return "String"

    # Integer
    if pg_type in ("smallint", "int2"):
        return "Int16"
    if pg_type in ("integer", "int", "int4"):
        return "Int32"
    if pg_type in ("bigint", "int8"):
        return "Int64"

    # Boolean
    if pg_type in ("boolean", "bool"):
        return "UInt8"

    # Numeric / Decimal — all use Float64 to avoid overflow
    if pg_type.startswith("numeric") or pg_type.startswith("decimal"):
        return "Float64"
    if pg_type in ("real", "double precision", "float4", "float8"):
        return "Float64"

    # Date / Time
    if pg_type == "date":
        return "Date"
    if pg_type in ("timestamp", "timestamp without time zone", "timestamp with time zone"):
        return "DateTime64(3)"

    # JSON
    if pg_type in ("json", "jsonb"):
        return "String"

    # Default fallback
    return "String"
