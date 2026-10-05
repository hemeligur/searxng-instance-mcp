"""MCP Server implementation for SearXNG web search."""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    ListToolsRequest,
    ListToolsResult,
    CallToolRequest,
    CallToolResult,
)

from .manager import SearXNGManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Server instance
APP_NAME = "searxng-web-search"
VERSION = "0.1.0"

server = Server(APP_NAME, version=VERSION)


async def list_tools_handler(
    ctx: ServerRequestContext, params: ListToolsRequest
) -> ListToolsResult:
    """Handle list_tools requests from MCP clients."""
    return ListToolsResult(
        tools=[
            Tool(
                name="web_search",
                description="Busca na web usando meta-buscador SearXNG com fallback automático entre instâncias",
                inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
            )
        ]
    )


async def call_tool_handler(
    ctx: ServerRequestContext, params: CallToolRequest
) -> CallToolResult:
    """Handle tool call requests from MCP clients."""
    name = params.name
    arguments = params.arguments or {}
    logger.info(f"call_tool called: {name}, args={arguments}")

    if name == "web_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required")

        limit = arguments.get("results_limit", 10)
        limit = max(1, min(int(limit), 50))

        try:
            manager = SearXNGManager()
            result = await manager.search(query, limit)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result.to_dict(), ensure_ascii=False))],
                is_error=not result.success,
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": str(e)}))],
                is_error=True,
            )

    raise ValueError(f"Unknown tool: {name}")


# Register handlers with the server (using string method names)
server.add_request_handler("tools/list", ListToolsRequest, list_tools_handler)
server.add_request_handler("tools/call", CallToolRequest, call_tool_handler)


async def main() -> None:
    """Main entry point for the MCP server.

    Starts the stdio-based MCP server that listens for client connections
    and exposes the web_search tool.
    """
    logger.info(f"Starting {APP_NAME} v{VERSION} MCP server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
