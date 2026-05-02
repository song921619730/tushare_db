"""Shared SQL escaping utilities for ClickHouse."""

from __future__ import annotations


def escape_sql_str(s: str) -> str:
    """Escape a string for use in ClickHouse SQL string literals.

    Handles both single quotes and backslashes to prevent SQL injection
    and malformed queries.
    """
    return s.replace("\\", "\\\\").replace("'", "''")
