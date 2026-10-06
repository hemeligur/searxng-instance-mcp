# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Hemeligur
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
