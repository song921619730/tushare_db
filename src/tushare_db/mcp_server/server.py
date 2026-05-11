"""MCP Server: stdio and streamable-http transport for Tushare DB."""

from __future__ import annotations

import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="tushare-db",
    instructions="Tushare Pro A-Share Data Warehouse — query market data via natural language",
)

# Import tools to register them
import tushare_db.mcp_server.tools  # noqa: E402, F401


def run_stdio() -> None:
    """Run MCP server over stdio transport."""
    mcp.run(transport="stdio")


def run_sse(host: str = "0.0.0.0", port: int = 7800) -> None:
    """Run MCP server over SSE transport for LAN access."""
    app = mcp.sse_app()
    uvicorn.run(app, host=host, port=port)
