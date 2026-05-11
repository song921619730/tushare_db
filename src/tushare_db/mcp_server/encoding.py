"""MCP response encoding: JSON for small results, Arrow IPC + LZ4 for large."""

from __future__ import annotations

import base64
import io
import json
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc


def encode_response(rows: list[dict[str, Any]], threshold: int = 1000) -> dict[str, Any]:
    """Encode rows. Returns a dict suitable for MCP tool response.

    For rows < threshold: plain JSON array in ``content``.
    For rows >= threshold: LZ4-compressed Arrow IPC, base64-encoded.
    """
    if len(rows) < threshold:
        return {
            "content": json.dumps(rows, ensure_ascii=False),
            "encoding": "json",
            "row_count": len(rows),
        }

    # Arrow IPC + LZ4
    table = pa.Table.from_pylist(rows)
    sink = io.BytesIO()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    raw = sink.getvalue()
    import lz4.frame
    compressed = lz4.frame.compress(raw, compression_level=3)
    encoded = base64.b64encode(compressed).decode("ascii")

    return {
        "content": encoded,
        "encoding": "arrow_ipc_lz4",
        "row_count": len(rows),
        "schema": str(table.schema),
    }


def decode_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Decode an MCP response back to a list of dicts.

    For JSON responses, parses ``response["content"]`` directly.
    For Arrow IPC + LZ4 responses, decodes the base64 payload.
    """
    if response["encoding"] == "json":
        return json.loads(response["content"])

    raw = base64.b64decode(response["content"])
    import lz4.frame
    decompressed = lz4.frame.decompress(raw)
    reader = ipc.open_stream(decompressed)
    table = reader.read_all()
    return table.to_pylist()
