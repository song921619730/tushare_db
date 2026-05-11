"""Schema module tests: inferer, ddl_builder.

Covers: sample loading, type inference, DDL generation.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestLoadSample:
    """inferer.py — load_sample."""

    def test_load_wrapped_tushare_format(self):
        """Tushare wraps fields/items under 'data' key."""
        from tushare_db.schema.inferer import load_sample

        sample = {
            "code": 0,
            "data": {
                "fields": ["ts_code", "trade_date", "close"],
                "items": [["000001.SZ", "20240101", 15.5]],
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample, f)
            f.flush()
            fields, rows = load_sample(f.name)

        assert fields == ["ts_code", "trade_date", "close"]
        assert len(rows) == 1
        assert rows[0] == {"ts_code": "000001.SZ", "trade_date": "20240101", "close": 15.5}

    def test_load_unwrapped_format(self):
        """Direct fields/items without 'data' wrapper."""
        from tushare_db.schema.inferer import load_sample

        sample = {
            "fields": ["a", "b"],
            "items": [[1, 2]],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample, f)
            f.flush()
            fields, rows = load_sample(f.name)

        assert fields == ["a", "b"]
        assert rows[0] == {"a": 1, "b": 2}

    def test_load_empty_items(self):
        """No items → empty rows list."""
        from tushare_db.schema.inferer import load_sample

        sample = {
            "data": {
                "fields": ["a"],
                "items": [],
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample, f)
            f.flush()
            fields, rows = load_sample(f.name)

        assert fields == ["a"]
        assert rows == []


class TestInferSchema:
    """inferer.py — infer_schema."""

    def test_infers_types_from_sample(self):
        from tushare_db.schema.inferer import infer_schema

        sample = {
            "data": {
                "fields": ["ts_code", "trade_date", "close"],
                "items": [
                    ["000001.SZ", "20240101", 15.5],
                    ["600519.SH", "20240102", 1800.0],
                ],
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample, f)
            f.flush()
            schema = infer_schema(f.name)

        col_map = {name: typ for name, typ in schema}
        assert col_map["ts_code"] == "LowCardinality(String)"
        assert col_map["trade_date"] == "Date"
        assert "Float64" in col_map["close"] or "Decimal64" in col_map["close"]
        # _version always appended
        assert col_map["_version"] == "UInt64"

    def test_overrides_applied(self):
        """YAML schema_overrides should override inferred types."""
        from tushare_db.schema.inferer import infer_schema

        sample = {
            "data": {
                "fields": ["custom_col"],
                "items": [[123]],
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample, f)
            f.flush()
            schema = infer_schema(f.name, overrides={"custom_col": "String"})

        col_map = {name: typ for name, typ in schema}
        assert col_map["custom_col"] == "String"


class TestBuildCreateTable:
    """ddl_builder.py — build_create_table."""

    def test_basic_create_table(self):
        from tushare_db.schema.ddl_builder import build_create_table

        ddl = build_create_table(
            "tushare.test_table",
            [("ts_code", "String"), ("trade_date", "Date"), ("close", "Float64")],
        )

        assert "CREATE TABLE IF NOT EXISTS tushare.test_table" in ddl
        assert "ReplacingMergeTree(_version)" in ddl
        assert "PARTITION BY tuple()" in ddl

    def test_custom_partition_and_order(self):
        from tushare_db.schema.ddl_builder import build_create_table

        ddl = build_create_table(
            "tushare.custom",
            [("ts_code", "String")],
            partition_key="toYYYYMM(trade_date)",
            order_by="ts_code",
        )

        assert "PARTITION BY toYYYYMM(trade_date)" in ddl
        assert "ORDER BY (ts_code)" in ddl

    def test_date_codec_applied(self):
        from tushare_db.schema.ddl_builder import build_create_table

        ddl = build_create_table(
            "tushare.test",
            [("trade_date", "Date")],
        )

        assert "CODEC(DoubleDelta, ZSTD(3))" in ddl

    def test_float_codec_applied(self):
        from tushare_db.schema.ddl_builder import build_create_table

        ddl = build_create_table(
            "tushare.test",
            [("close", "Float64")],
        )

        assert "CODEC(Gorilla, ZSTD(3))" in ddl

    def test_float_codec_not_applied_to_unrelated(self):
        """Float codec only for price-related columns."""
        from tushare_db.schema.ddl_builder import build_create_table

        ddl = build_create_table(
            "tushare.test",
            [("some_metric", "Float64")],
        )

        # No CODEC for non-price Float64
        assert "CODEC" not in ddl


class TestBuildCreateTablesBatch:
    """ddl_builder.py — build_create_tables_batch."""

    def test_multiple_tables(self):
        from tushare_db.schema.ddl_builder import build_create_tables_batch

        tables = {
            "tushare.daily": ([("ts_code", "String")], "tuple()", "ts_code, trade_date"),
            "tushare.weekly": ([("ts_code", "String")], "tuple()", "ts_code, trade_date"),
        }
        ddls = build_create_tables_batch(tables)
        assert len(ddls) == 2
        assert any("tushare.daily" in d for d in ddls)
        assert any("tushare.weekly" in d for d in ddls)


class TestInferSchemasBatch:
    """inferer.py — infer_schemas_batch."""

    def test_missing_sample_skipped(self):
        from tushare_db.schema.inferer import infer_schemas_batch

        results = infer_schemas_batch("/nonexistent", {"missing": (None, None)})
        assert results == {}

    def test_batch_infers_multiple(self):
        from tushare_db.schema.inferer import infer_schemas_batch

        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["daily", "weekly"]:
                sample = {
                    "data": {
                        "fields": ["ts_code", "close"],
                        "items": [["000001.SZ", 15.5]],
                    },
                }
                with open(Path(tmpdir) / f"{name}.json", "w") as f:
                    json.dump(sample, f)

            results = infer_schemas_batch(tmpdir, {
                "daily": (None, None),
                "weekly": (None, None),
            })

            assert "daily" in results
            assert "weekly" in results
