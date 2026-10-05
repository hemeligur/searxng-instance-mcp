"""SearXNG Instance MCP Server.

A Model Context Protocol server that provides web search functionality
via SearXNG meta-search engine with automatic instance fallback.
"""

from searxng_mcp.server import main

__version__ = "0.1.0"
__all__ = ["main"]
