"""MCP Server implementation for SearXNG web search."""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .manager import SearXNGManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Server instance
APP_NAME = "searxng-web-search"
server = Server(APP_NAME)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools exposed by this MCP server.

    Returns:
        List containing the web_search tool definition.
    """
    return [
        Tool(
            name="web_search",
            description="Busca na web usando meta-buscador SearXNG com fallback automático entre instâncias",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca para pesquisar na web",
                    },
                    "results_limit": {
                        "type": "number",
                        "description": "Número máximo de resultados a retornar (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from MCP clients.

    Args:
        name: The name of the tool being called.
        arguments: The arguments passed to the tool.

    Returns:
        List of TextContent objects containing the search results or error.

    Raises:
        ValueError: If the tool name is unknown or arguments are invalid.
    """
    if name == "web_search":
        query = arguments.get("query")
        if not query or not isinstance(query, str):
            raise ValueError("Invalid query: must be a non-empty string")

        limit = arguments.get("results_limit", 10)
        if not isinstance(limit, (int, float)):
            limit = 10
        limit = max(1, min(int(limit), 50))  # Clamp between 1 and 50

        logger.info(f"Processing web_search: query='{query}', limit={limit}")

        try:
            manager = SearXNGManager()
            result = await manager.search(query, limit)
            result_dict = result.to_dict()

            logger.info(
                f"Search completed: success={result.success}, "
                f"results={result.count}, instance={result.instance_used}"
            )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result_dict, ensure_ascii=False, indent=2),
                )
            ]

        except Exception as e:
            logger.error(f"Search failed with exception: {e}")
            error_response = {
                "success": False,
                "query": query,
                "error": "Search execution failed",
                "message": str(e),
            }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(error_response, ensure_ascii=False, indent=2),
                )
            ]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    """Main entry point for the MCP server.

    Starts the stdio-based MCP server that listens for client connections
    and exposes the web_search tool.
    """
    logger.info(f"Starting {APP_NAME} MCP server...")

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
