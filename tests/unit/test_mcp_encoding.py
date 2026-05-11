"""Unit tests for B9 fix: MCP Arrow IPC + LZ4 encoding."""

from __future__ import annotations

import json
import pytest

from tushare_db.mcp_server.encoding import encode_response


class TestEncodeResponse:
    """B9: Verify encoding thresholds and output format."""

    def test_small_result_returns_json(self):
        """< 1000 rows should return JSON."""
        rows = [{"a": 1, "b": "x"} for _ in range(100)]
        result = encode_response(rows)
        assert result["encoding"] == "json"
        assert result["row_count"] == 100
        # Content should be parseable JSON
        parsed = json.loads(result["content"])
        assert len(parsed) == 100

    def test_large_result_returns_arrow_ipc_lz4(self):
        """>= 1000 rows should return Arrow IPC + LZ4."""
        rows = [{"a": i, "b": f"row_{i}"} for i in range(1500)]
        result = encode_response(rows)
        assert result["encoding"] == "arrow_ipc_lz4"
        assert result["row_count"] == 1500
        assert "schema" in result
        # Content should be valid base64
        import base64
        decoded = base64.b64decode(result["content"])
        assert len(decoded) > 0

    def test_threshold_boundary(self):
        """Exactly 1000 rows should trigger Arrow encoding."""
        rows = [{"a": i} for i in range(1000)]
        result = encode_response(rows)
        assert result["encoding"] == "arrow_ipc_lz4"

    def test_999_rows_returns_json(self):
        """999 rows should still be JSON."""
        rows = [{"a": i} for i in range(999)]
        result = encode_response(rows)
        assert result["encoding"] == "json"

    def test_empty_rows_returns_json(self):
        """Empty list should return JSON."""
        result = encode_response([])
        assert result["encoding"] == "json"
        assert result["row_count"] == 0
        assert result["content"] == "[]"

    def test_arrow_roundtrip(self):
        """Arrow IPC + LZ4 should decode back to original data."""
        import base64
        import io
        import pyarrow as pa
        import pyarrow.ipc as ipc
        import lz4.frame

        rows = [{"a": i, "b": f"row_{i}"} for i in range(2000)]
        result = encode_response(rows)

        assert result["encoding"] == "arrow_ipc_lz4"

        # Decode
        compressed = base64.b64decode(result["content"])
        raw = lz4.frame.decompress(compressed)
        table = ipc.open_stream(io.BytesIO(raw)).read_all()
        decoded = table.to_pylist()

        assert len(decoded) == 2000
        assert decoded[0]["a"] == 0
        assert decoded[1999]["a"] == 1999

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        rows = [{"a": i} for i in range(50)]
        result = encode_response(rows, threshold=10)
        assert result["encoding"] == "arrow_ipc_lz4"
