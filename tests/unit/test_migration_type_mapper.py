"""Unit tests: migration type mapper."""

import pytest
from tushare_db.migration.type_mapper import pg_type_to_ch


@pytest.mark.parametrize("pg_type,col,expected", [
    ("character varying", "ts_code", "LowCardinality(String)"),
    ("character varying", "name", "String"),
    ("integer", "x", "Int32"),
    ("bigint", "x", "Int64"),
    ("numeric", "x", "Float64"),
    ("numeric(18,4)", "x", "Float64"),
    ("date", "trade_date", "Date"),
    ("timestamp without time zone", "x", "DateTime64(3)"),
    ("boolean", "is_open", "UInt8"),
    ("jsonb", "data", "String"),
    ("smallint", "x", "Int16"),
    ("double precision", "x", "Float64"),
    ("decimal", "x", "Float64"),
    ("text", "description", "String"),
    ("timestamp with time zone", "x", "DateTime64(3)"),
])
def test_pg_type_to_ch(pg_type, col, expected):
    assert pg_type_to_ch(pg_type, col) == expected
