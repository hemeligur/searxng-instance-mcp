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

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


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

    # TTL for circuit breaker in seconds
    CIRCUIT_TTL: float = field(default=300, repr=False)  # 5 minutes

    def is_available(self) -> bool:
        """Check if instance is available for requests."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return True
        else:  # OPEN
            # Check if TTL has passed
            if self.circuit_open_at is not None:
                import time

                if time.time() - self.circuit_open_at >= self.CIRCUIT_TTL:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

    def record_success(self) -> None:
        """Record a successful request."""
        import time

        self.state = CircuitState.CLOSED
        self.last_success = time.time()
        self.failure_count = 0
        self.error_message = None

    def record_failure(self, error: str) -> None:
        """Record a failed request."""
        import time

        self.failure_count += 1
        self.last_failure = time.time()
        self.error_message = error

        # Open circuit after 3 consecutive failures
        if self.failure_count >= 3:
            self.state = CircuitState.OPEN
            self.circuit_open_at = time.time()


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

        return result


@dataclass
class DiscoveredInstance:
    """Instance discovered from searx.space API."""

    name: str
    url: str
    uptime: float
    tls_rank: str
    engines: list[str]

    @classmethod
    def from_api_response(cls, data: dict) -> "DiscoveredInstance":
        """Create from searx.space API response."""
        network = data.get("network", {})
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            uptime=network.get("uptime", 0),
            tls_rank=network.get("tls_rank", ""),
            engines=data.get("engines", []),
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
