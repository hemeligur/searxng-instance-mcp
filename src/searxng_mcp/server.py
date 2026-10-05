"""MCP Server implementation for SearXNG web search."""

import asyncio
import sys


async def async_main() -> None:
    """Async main entry point."""
    print("SearXNG MCP Server - Use uv run to start", file=sys.stderr)


def main() -> None:
    """Main entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
