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

from .manager import async_get_manager
from .constants import is_debug_enabled

# Create FastMCP server
mcp = FastMCP("searxng-web-search", version="0.2.0")


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
    manager = await async_get_manager()
    result = await manager.search(query, limit)
    return json.dumps(result.to_dict(), ensure_ascii=False)


# =============================================================================
# DEBUG TOOLS - Registered conditionally based on SEARXNG_DEBUG_TOOLS env var
# =============================================================================

def _register_debug_tools() -> None:
    """Register debug tools if SEARXNG_DEBUG_TOOLS=true."""
    
    @mcp.tool()
    async def get_instances_status() -> str:
        """Retorna o status de todas as instâncias SearXNG gerenciadas.
        
        Inclui:
        - Total de instâncias
        - Instâncias disponíveis vs em backoff/circuit breaker
        - Contagem de falhas por instância
        - Tempo restante de backoff
        
        Returns:
            JSON string com status detalhado
        """
        manager = await async_get_manager()
        return json.dumps(manager.get_status_summary(), ensure_ascii=False, indent=2)


    @mcp.tool()
    async def reset_instance(url: str = "") -> str:
        """Reseta o estado de uma instância ou todas as instâncias.
        
        Use para limpar backoff e circuit breaker quando quiser
        forçar o uso de uma instância específica.
        
        Args:
            url: URL da instância para resetar, ou vazio para resetar todas
            
        Returns:
            JSON string com resultado do reset
        """
        manager = await async_get_manager()
        target = url if url else None
        result = manager.reset_instance(target)
        return json.dumps(result, ensure_ascii=False)


    @mcp.tool()
    async def get_available_instances() -> str:
        """Lista instâncias atualmente disponíveis para uso.
        
        Retorna apenas instâncias que não estão em backoff
        e cujo circuit breaker permite requisições.
        
        Returns:
            JSON string com lista de instâncias disponíveis
        """
        manager = await async_get_manager()
        return json.dumps(manager.get_available_instances(), ensure_ascii=False, indent=2)


# Register debug tools based on config
if is_debug_enabled():
    _register_debug_tools()


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
