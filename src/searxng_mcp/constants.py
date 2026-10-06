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

"""
Constantes e configurações do searxng-mcp.

Este módulo define todas as constantes utilizadas pelo projeto,
incluindo instâncias fallback, timeouts, e configurações de cache.
"""

from pathlib import Path

# =============================================================================
# INSTÂNCIAS FALLBACK
# =============================================================================

FALLBACK_INSTANCES: list[str] = [
    "https://sx.xo.st",
    "https://search.ctq.ro",
    "https://xka.cz",
    "https://www.isci.si",
]
"""Lista de instâncias SearXNG hardcoded como fallback quando o discovery falha."""


# =============================================================================
# CONFIGURAÇÕES DE REQUISIÇÃO
# =============================================================================

DEFAULT_TIMEOUT: int = 10
"""Tempo máximo em segundos para等待 uma resposta da instância."""

DEFAULT_LIMIT: int = 10
"""Número padrão de resultados por busca."""

# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

CIRCUIT_BREAKER_TTL: int = 300
"""Tempo de vida do estado OPEN do circuit breaker em segundos (5 minutos)."""

# =============================================================================
# CACHE
# =============================================================================

CACHE_TTL: int = 3600
"""Tempo de vida do cache de instâncias em segundos (1 hora)."""

CACHE_DIR: Path = Path.home() / ".cache" / "searxng-mcp"
"""Diretório base para arquivos de cache do projeto."""

# =============================================================================
# FILTROS DE INSTÂNCIA
# =============================================================================

MAX_INSTANCES: int = 20
"""Número máximo de instâncias no pool de instâncias ativas."""

MIN_UPTIME: float = 95.0
"""Uptime mínimo aceito para uma instância (%).

Instâncias com uptime abaixo deste valor são descartadas.
"""

REQUIRED_TLS_RANKS: list[str] = ["A+", "A"]
"""Classificações TLS mínimas aceitas para uma instância.

Instâncias com classificação inferior são descartadas por segurança.
"""

REQUIRED_ENGINES: list[str] = ["google", "bing", "duckduckgo"]
"""Lista de motores de busca que uma instância deve suportar.

Uma instância é considerada válida apenas se tiver todos estes motores.
"""

# =============================================================================
# API
# =============================================================================

SEARX_API_URL: str = "https://searx.space/api/v1/instances"
"""URL da API do searx.space para descoberta de instâncias."""
