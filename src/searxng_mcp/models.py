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

"""Data models for SearXNG MCP server."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


# --- Scoring Constants ---

# TLS grades scores
TLS_GRADE_SCORES = {
    "A+": 1.0, "A": 0.9, "B": 0.7, "C": 0.5, "D": 0.3, "E": 0.1
}
# Score para grades TLS desconhecidos
TLS_UNKNOWN_FALLBACK = 0.3

# Componente Externo: soma dos pesos = 0.40
EXTERNAL_MAX_WEIGHT = 0.20 + 0.15 + 0.05
# Score fallback quando não há métricas externas
DEFAULT_EXTERNAL_CONTRIBUTION = 0.12

# Componente Interno: soma dos pesos = 0.60
INTERNAL_MAX_WEIGHT = 0.35 + 0.15 + 0.10
# Score fallback para divisão por zero
DEFAULT_INTERNAL_CONTRIBUTION = 0.3


@dataclass
class ExternalMetrics:
    """Dados externos da API searx.space para scoring híbrido.

    Estes dados são cacheados e atualizados a cada ciclo de discovery.
    Usados no componente externo (50%) do score de tier.
    """

    uptime_day: float = 0.0
    uptime_week: float = 0.0
    tls_grade: str = "C"
    engine_count: int = 0
    error_load: float = 0.0
    error_check: float = 0.0
    network_country: str = ""
    last_updated: Optional[float] = None  # timestamp

    def __post_init__(self):
        """Set timestamp se não fornecido."""
        if self.last_updated is None:
            self.last_updated = time.time()

    def to_dict(self) -> dict:
        """Serialize to dictionary for persistence."""
        return {
            "uptime_day": self.uptime_day,
            "uptime_week": self.uptime_week,
            "tls_grade": self.tls_grade,
            "engine_count": self.engine_count,
            "error_load": self.error_load,
            "error_check": self.error_check,
            "network_country": self.network_country,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalMetrics":
        """Deserialize from dictionary."""
        return cls(
            uptime_day=data.get("uptime_day", 0.0),
            uptime_week=data.get("uptime_week", 0.0),
            tls_grade=data.get("tls_grade", "C"),
            engine_count=data.get("engine_count", 0),
            error_load=data.get("error_load", 0.0),
            error_check=data.get("error_check", 0.0),
            network_country=data.get("network_country", ""),
            last_updated=data.get("last_updated"),
        )


@dataclass
class InstanceStatus:
    """Status tracking for a SearXNG instance."""

    url: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure: Optional[float] = None  # timestamp
    last_success: Optional[float] = None  # timestamp
    circuit_open_at: Optional[float] = None  # timestamp when circuit opened
    error_message: Optional[str] = None
    disabled: bool = False  # Explicitly disabled by user config

    # Exponential backoff settings
    backoff_until: Optional[float] = None  # timestamp when backoff ends
    BACKOFF_BASE: float = field(default=60, repr=False)  # Base backoff: 60 seconds
    BACKOFF_MAX: float = field(default=900, repr=False)  # Max backoff: 15 minutes
    BACKOFF_MULTIPLIER: float = field(default=2.0, repr=False)  # Exponential factor

    # TTL for circuit breaker in seconds
    CIRCUIT_TTL: float = field(default=300, repr=False)  # 5 minutes

    # Métricas internas para scoring (componente interno do score híbrido)
    total_requests: int = 0
    successful_requests: int = 0
    response_times_ms: list[float] = field(default_factory=list)

    # Cache de métricas externas da API searx.space
    _external_metrics: Optional[ExternalMetrics] = field(default=None, repr=False)
    _last_external_update: Optional[float] = field(default=None, repr=False)

    # Recency decay: half-life de 1 hora
    RECENCY_HALF_LIFE: float = field(default=3600.0, repr=False)

    # --- Scoring Methods ---

    @property
    def success_rate(self) -> float:
        """Calcula taxa de sucesso das requisições.

        Returns:
            Float entre 0.0 e 1.0. Retorna 0.5 se não há histórico.
        """
        if self.total_requests == 0:
            return 0.5
        return self.successful_requests / self.total_requests

    @property
    def circuit_score(self) -> float:
        """Score baseado no estado do circuit breaker.

        Returns:
            1.0 (CLOSED), 0.5 (HALF_OPEN), 0.0 (OPEN)
        """
        return {
            CircuitState.CLOSED: 1.0,
            CircuitState.HALF_OPEN: 0.5,
            CircuitState.OPEN: 0.0,
        }.get(self.state, 0.0)

    def _calculate_recency_bonus(self) -> float:
        """Calcula bonus de recência com decay exponencial.

        Retorna valor entre 0.5 e 1.0 baseado em quão recente foi o último sucesso.
        Usa half-life de 1 hora: score = 0.5 + (0.5 * decay)

        Returns:
            Float entre 0.5 (muito antigo) e 1.0 (agora mesmo)
        """
        if self.last_success is None:
            return 0.5  # Neutro sem dados

        elapsed = time.time() - self.last_success

        # Decay exponencial: 0.5 ^ (elapsed / half_life)
        decay = 0.5 ** (elapsed / self.RECENCY_HALF_LIFE)
        return 0.5 + (0.5 * decay)

    @property
    def external_metrics(self) -> Optional[ExternalMetrics]:
        """Retorna métricas externas cacheadas."""
        return self._external_metrics

    def update_external_metrics(self, metrics: ExternalMetrics) -> None:
        """Atualiza métricas externas da API searx.space.

        Args:
            metrics: ExternalMetrics com dados da API
        """
        self._external_metrics = metrics
        self._last_external_update = time.time()

    def calculate_tier_score(self) -> float:
        """Calcula score híbrido para classificação em tier.

        Score = ScoreExterno(40%) + ScoreInterno(60%)

        Componente Externo (máx 0.4):
        - uptime (20%): uptime_day / 100
        - tls (15%): A+=1.0, A=0.9, B=0.7, C=0.5, D=0.3, E=0.1
        - engines (5%): min(engine_count / 20, 1.0)

        Componente Interno (máx 0.6):
        - success_rate (35%): successful_requests / total_requests
        - recency (15%): bonus com decay exponencial
        - circuit (10%): CLOSED=1.0, HALF_OPEN=0.5, OPEN=0.0

        Returns:
            Float entre 0.0 e 1.0 (máximo = 1.0 para instância perfeita)
        """
        # Componente Externo (40% do score total)
        external = 0.0
        if self._external_metrics:
            uptime_score = self._external_metrics.uptime_day / 100.0
            tls_score = TLS_GRADE_SCORES.get(self._external_metrics.tls_grade, TLS_UNKNOWN_FALLBACK)
            engine_score = min(self._external_metrics.engine_count / 20.0, 1.0)

            # Normalizar para máximo de 0.4
            external_raw = (
                uptime_score * 0.20 +
                tls_score * 0.15 +
                engine_score * 0.05
            )
            external = (
                (external_raw / EXTERNAL_MAX_WEIGHT) * 0.4
                if EXTERNAL_MAX_WEIGHT > 0
                else DEFAULT_EXTERNAL_CONTRIBUTION
            )
        else:
            external = 0.0  # Sem contribuição se não há dados externos

        # Componente Interno (60% do score total)
        internal_raw = (
            self.success_rate * 0.35 +
            self._calculate_recency_bonus() * 0.15 +
            self.circuit_score * 0.10
        )
        # Normalizar para máximo de 0.6
        internal = (
            (internal_raw / INTERNAL_MAX_WEIGHT) * 0.6
            if INTERNAL_MAX_WEIGHT > 0
            else DEFAULT_INTERNAL_CONTRIBUTION
        )

        # Score final ponderado (máximo = 1.0)
        return external + internal

    def get_tier(self) -> int:
        """Retorna tier baseado no score calculado.

        Returns:
            1 (Premium): score >= 0.70
            2 (Standard): score >= 0.45
            3 (Risky): score < 0.45
        """
        score = self.calculate_tier_score()
        if score >= 0.70:
            return 1
        elif score >= 0.45:
            return 2
        return 3

    def record_request(self, success: bool, response_time_ms: Optional[float] = None) -> None:
        """Registra resultado de uma requisição.

        Args:
            success: True se a requisição foi bem sucedida
            response_time_ms: Tempo de resposta em milliseconds (opcional)
        """
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.last_success = time.time()
        if response_time_ms is not None:
            self.response_times_ms.append(response_time_ms)
            # Manter apenas últimos 10 tempos de resposta
            self.response_times_ms = self.response_times_ms[-10:]

    # --- Existing Methods ---

    def is_available(self) -> bool:
        """Check if instance is available for requests."""
        import time

        # Explicitly disabled instances are never available
        if self.disabled:
            return False

        # Check exponential backoff first
        if self.backoff_until is not None and time.time() < self.backoff_until:
            return False

        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return True
        else:  # OPEN
            # Check if TTL has passed
            if self.circuit_open_at is not None:
                if time.time() - self.circuit_open_at >= self.CIRCUIT_TTL:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

    def get_backoff_seconds(self) -> int:
        """Calculate backoff seconds based on failure count.

        Returns:
            Backoff duration in seconds.
        """

        if self.failure_count <= 1:
            return int(self.BACKOFF_BASE)

        # Exponential backoff: base * multiplier^(failure_count - 1)
        backoff = self.BACKOFF_BASE * (self.BACKOFF_MULTIPLIER ** (self.failure_count - 1))
        return min(int(backoff), int(self.BACKOFF_MAX))

    def record_success(self) -> None:
        """Record a successful request."""
        import time

        self.state = CircuitState.CLOSED
        self.last_success = time.time()
        self.failure_count = 0
        self.error_message = None
        self.backoff_until = None  # Clear backoff on success

    def record_failure(self, error: str) -> None:
        """Record a failed request and apply exponential backoff."""
        import time

        self.failure_count += 1
        self.last_failure = time.time()
        self.error_message = error

        # Apply exponential backoff
        backoff_seconds = self.get_backoff_seconds()
        self.backoff_until = time.time() + backoff_seconds

        # Open circuit after 3 consecutive failures
        if self.failure_count >= 3:
            self.state = CircuitState.OPEN
            self.circuit_open_at = time.time()

    def get_backoff_remaining(self) -> Optional[float]:
        """Get remaining backoff time in seconds.

        Returns:
            Seconds remaining or None if no backoff active.
        """
        import time

        if self.backoff_until is None:
            return None

        remaining = self.backoff_until - time.time()
        return max(0, remaining)

    def reset(self) -> None:
        """Reset all state for this instance."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure = None
        self.last_success = None
        self.circuit_open_at = None
        self.error_message = None
        self.backoff_until = None

    @classmethod
    def from_dict(cls, data: dict) -> "InstanceStatus":
        """Create InstanceStatus from dictionary (for deserialization).

        Args:
            data: Dictionary with serialized instance state

        Returns:
            InstanceStatus instance
        """
        # Handle missing fields for backward compatibility
        external_metrics_data = data.get("external_metrics")
        external_metrics = (
            ExternalMetrics.from_dict(external_metrics_data)
            if external_metrics_data
            else None
        )

        instance = cls(
            url=data["url"],
            state=CircuitState(data.get("state", "closed")),
            failure_count=data.get("failure_count", 0),
            last_failure=data.get("last_failure"),
            last_success=data.get("last_success"),
            circuit_open_at=data.get("circuit_open_at"),
            error_message=data.get("error_message"),
            disabled=data.get("disabled", False),
            backoff_until=data.get("backoff_until"),
            # Métricas internas
            total_requests=data.get("total_requests", 0),
            successful_requests=data.get("successful_requests", 0),
            response_times_ms=data.get("response_times_ms", []),
            _external_metrics=external_metrics,
            _last_external_update=data.get("last_external_update"),
        )
        return instance

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure,
            "last_success": self.last_success,
            "circuit_open_at": self.circuit_open_at,
            "error_message": self.error_message,
            "backoff_until": self.backoff_until,
            "backoff_remaining": self.get_backoff_remaining(),
            "backoff_seconds": self.get_backoff_seconds(),
            "disabled": self.disabled,
            # Métricas internas para scoring
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "response_times_ms": self.response_times_ms,
            # Métricas externas (serializadas)
            "external_metrics": (
                self._external_metrics.to_dict() if self._external_metrics else None
            ),
            "last_external_update": self._last_external_update,
        }


@dataclass
class SearchResult:
    """Single search result from SearXNG."""

    url: str
    title: str
    content: str
    engine: str
    category: str = "general"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "engine": self.engine,
        }


@dataclass
class SearchResponse:
    """Response from web search operation."""

    success: bool
    query: str
    results: list[SearchResult] = field(default_factory=list)
    count: int = 0
    instance_used: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None
    details: list[dict] = field(default_factory=list)
    rate_limited: bool = False  # True when empty results are likely due to rate limiting

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        result = {
            "success": self.success,
            "query": self.query,
        }

        if self.success:
            result["results"] = [r.to_dict() for r in self.results]
            result["count"] = self.count
            result["instance_used"] = self.instance_used
        else:
            result["error"] = self.error
            result["message"] = self.message
            result["details"] = self.details
            if self.rate_limited:
                result["rate_limited"] = True

        return result


@dataclass
class DiscoveredInstance:
    """Instance discovered from searx.space API.

    Contém todos os dados disponíveis na API searx.space para uma instância.
    """

    name: str
    url: str
    uptime: float
    tls_rank: str
    engines: list[str]

    # Campos adicionais da API (TIER-002)
    error_load: float = 0.0
    error_check: float = 0.0
    network_country: str = ""
    network_region: str = ""
    uptime_week: float = 0.0

    @classmethod
    def from_api_response(cls, url: str, data: dict) -> "DiscoveredInstance":
        """Create from searx.space API response.

        Args:
            url: The instance URL (used as key in the API response).
            data: The instance data dictionary from the API.

        Returns:
            DiscoveredInstance instance.
        """
        # New format has uptime directly under 'uptime' key
        uptime_data = data.get("uptime", {})
        uptime = uptime_data.get("uptimeDay", uptime_data.get("uptimeWeek", 0))

        # TLS grade is in tls.grade
        tls = data.get("tls", {})
        tls_rank = tls.get("grade", "")

        # Engines is now a dict, extract engine names
        engines_data = data.get("engines", {})
        engine_names = list(engines_data.keys()) if engines_data else []

        # Extract name from alternativeUrls or use URL
        alt_urls = data.get("alternativeUrls", {})
        name = url if not alt_urls else list(alt_urls.values())[0] if alt_urls else url

        # Novos campos (TIER-002)
        error_load = data.get("error_load", 0.0)
        error_check = data.get("error_check", 0.0)
        network = data.get("network", {})
        network_country = network.get("country", "") if network else ""
        network_region = network.get("region", "") if network else ""

        # Uptime week está disponível no mesmo dict de uptime
        uptime_week = uptime_data.get("uptimeWeek", 0)

        return cls(
            name=name,
            url=url,
            uptime=uptime,
            tls_rank=tls_rank,
            engines=engine_names,
            error_load=error_load,
            error_check=error_check,
            network_country=network_country,
            network_region=network_region,
            uptime_week=uptime_week,
        )

    def is_healthy(self) -> bool:
        """Check if instance meets health criteria."""
        # Minimum uptime threshold
        if self.uptime < 95:
            return False
        # TLS rank should be A or A+
        if self.tls_rank not in ("A+", "A"):
            return False
        return True
