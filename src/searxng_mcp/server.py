"""MCP Server implementation for SearXNG web search using FastMCP."""

import json

from fastmcp import FastMCP

from .manager import SearXNGManager

# Create FastMCP server
mcp = FastMCP("searxng-web-search", version="0.1.0")


@mcp.tool()
async def web_search(query: str, results_limit: int = 10) -> str:
    """Busca na web usando meta-buscador SearXNG com fallback automático.

    Args:
        query: Termo de busca
        results_limit: Número máximo de resultados (1-50, padrão 10)

    Returns:
        JSON string com resultados da busca
    """
    limit = max(1, min(results_limit, 50))
    manager = SearXNGManager()
    result = await manager.search(query, limit)
    return json.dumps(result.to_dict(), ensure_ascii=False)


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
