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

"""SearXNG Manager - Pool management and search execution with circuit breaker."""

import asyncio
import logging
import random
from typing import Optional

import httpx

from .constants import DEFAULT_LIMIT, DEFAULT_TIMEOUT
from .discovery import discover_instances, get_fallback_instances
from .models import CircuitState, InstanceStatus, SearchResponse, SearchResult
from .persistence import load_instance_states, save_instance_states

logger = logging.getLogger(__name__)


# Global singleton instance
_manager_instance: Optional["SearXNGManager"] = None
_manager_lock = asyncio.Lock()


def get_manager() -> "SearXNGManager":
    """Get the singleton SearXNGManager instance.
    
    Returns:
        The singleton manager instance.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SearXNGManager()
    return _manager_instance


async def async_get_manager() -> "SearXNGManager":
    """Get the singleton manager instance asynchronously.
    
    This is the preferred method when called from async context.
    
    Returns:
        The singleton manager instance.
    """
    global _manager_instance
    if _manager_instance is None:
        async with _manager_lock:
            if _manager_instance is None:
                _manager_instance = SearXNGManager()
                await _manager_instance._async_initialize()
    return _manager_instance


class SearXNGManager:
    """Manages a pool of SearXNG instances with circuit breaker pattern.

    Features:
    - Automatic instance discovery from searx.space
    - Circuit breaker with CLOSED → OPEN → HALF_OPEN states
    - Exponential backoff (60s base, 15min max)
    - Persistent state across server restarts
    - Random instance selection for load distribution
    - Automatic fallback to hardcoded instances
    """

    def __init__(self) -> None:
        """Initialize the SearXNG manager."""
        self.instances: dict[str, InstanceStatus] = {}
        self._initialized = False
        self._dirty = False  # Track if state needs to be saved
        
        # Load persisted state
        self._load_persisted_state()

    def _load_persisted_state(self) -> None:
        """Load persisted instance states from disk."""
        try:
            persisted = load_instance_states()
            # Merge with existing instances, preserving state
            for url, status in persisted.items():
                self.instances[url] = status
            if persisted:
                logger.info(f"Loaded {len(persisted)} persisted instance states")
        except Exception as e:
            logger.warning(f"Failed to load persisted state: {e}")

    def save_state(self) -> bool:
        """Save current instance states to disk.
        
        Returns:
            True if saved successfully.
        """
        if not self._dirty:
            return True
            
        try:
            success = save_instance_states(self.instances)
            if success:
                self._dirty = False
            return success
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def _mark_dirty(self) -> None:
        """Mark state as modified, needs saving."""
        self._dirty = True

    async def _async_initialize(self) -> None:
        """Initialize instances asynchronously."""
        if self._initialized:
            return
            
        try:
            # Try to discover instances from searx.space
            instances = await discover_instances(use_cache=True)
            
            # Add new instances, preserving existing state
            for url in instances:
                if url not in self.instances:
                    self.instances[url] = InstanceStatus(url=url)
                self._mark_dirty()
            
            # Shuffle for load distribution
            self._shuffle_instances()
            
            logger.info(f"Initialized with {len(self.instances)} instances")
            self._initialized = True
            
            # Save state after initialization
            self.save_state()
            
        except Exception as e:
            logger.warning(f"Failed to discover instances: {e}, using fallback")
            await self._load_fallback_instances_async()

    def _shuffle_instances(self) -> None:
        """Shuffle instance order for load distribution."""
        urls = list(self.instances.keys())
        random.shuffle(urls)
        # Recreate dict in new order
        self.instances = {url: self.instances[url] for url in urls}

    async def _load_fallback_instances_async(self) -> None:
        """Load fallback instances asynchronously."""
        fallback_urls = get_fallback_instances()
        for url in fallback_urls:
            if url not in self.instances:
                self.instances[url] = InstanceStatus(url=url)
        self._shuffle_instances()
        logger.info(f"Loaded {len(fallback_urls)} fallback instances")
        self._initialized = True
        self._mark_dirty()

    def _update_instance_status(
        self, url: str, success: bool, error: Optional[str] = None
    ) -> None:
        """Update the circuit breaker status for an instance.

        Args:
            url: The instance URL.
            success: Whether the request was successful.
            error: Error message if the request failed.
        """
        if url not in self.instances:
            logger.warning(f"Unknown instance: {url}")
            return

        status = self.instances[url]

        if success:
            status.record_success()
            logger.debug(f"Instance {url}: success, circuit CLOSED")
        else:
            status.record_failure(error or "Unknown error")
            backoff_secs = status.get_backoff_seconds()
            logger.debug(
                f"Instance {url}: failure ({error}), "
                f"state={status.state.value}, failures={status.failure_count}, "
                f"backoff={backoff_secs}s"
            )
        
        self._mark_dirty()

    async def search(self, query: str, limit: int = DEFAULT_LIMIT) -> SearchResponse:
        """Execute a search query using available SearXNG instances.

        Tries instances in order, implementing circuit breaker pattern:
        - CLOSED: Normal operation, requests allowed
        - OPEN: After 3 failures, requests blocked until TTL expires
        - HALF_OPEN: After TTL, allows one test request

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            SearchResponse with results if successful, or error details if all
            instances failed.
        """
        # Ensure initialized
        if not self._initialized:
            await self._async_initialize()
        
        # Save state before making requests
        self.save_state()

        if not query or not query.strip():
            return SearchResponse(
                success=False,
                query=query,
                error="Empty query",
                message="Search query cannot be empty",
            )

        query = query.strip()

        # Try each available instance
        errors: list[dict] = []
        skipped: list[str] = []

        for url, status in self.instances.items():
            # Check availability (includes backoff check)
            if not status.is_available():
                backoff_remaining = status.get_backoff_remaining()
                if backoff_remaining and backoff_remaining > 0:
                    skipped.append(f"{url} (backoff: {backoff_remaining:.0f}s)")
                else:
                    skipped.append(f"{url} (circuit: {status.state.value})")
                continue

            # Attempt search on this instance
            try:
                result = await self._try_instance(url, query, limit)
                if result.success:
                    result.instance_used = url
                    self._update_instance_status(url, success=True)
                    # Save state after successful request
                    self.save_state()
                    return result
                else:
                    errors.append({
                        "instance": url,
                        "error": result.error,
                        "rate_limited": result.rate_limited,
                    })
                    self._update_instance_status(url, success=False, error=result.error)

            except httpx.TimeoutException:
                error_msg = "Request timeout"
                errors.append({"instance": url, "error": error_msg})
                self._update_instance_status(url, success=False, error=error_msg)
                logger.warning(f"Timeout on {url}")

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                errors.append({"instance": url, "error": error_msg})
                self._update_instance_status(url, success=False, error=error_msg)
                logger.warning(f"HTTP error on {url}: {e.response.status_code}")

            except httpx.RequestError as e:
                error_msg = f"Request error: {type(e).__name__}"
                errors.append({"instance": url, "error": error_msg})
                self._update_instance_status(url, success=False, error=error_msg)
                logger.warning(f"Request error on {url}: {e}")

            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}"
                errors.append({"instance": url, "error": error_msg})
                self._update_instance_status(url, success=False, error=error_msg)
                logger.error(f"Unexpected error on {url}: {e}")

        # All instances failed
        logger.error(f"All {len(errors)} instances failed for query: {query}")

        # Check if any instance was rate limited
        any_rate_limited = any(
            isinstance(e, dict) and e.get("rate_limited") for e in errors
        )

        # Build response with skipped info
        response = SearchResponse(
            success=False,
            query=query,
            error="All instances unavailable",
            message=f"Failed to search using any available instance. "
            f"{len(skipped)} instances skipped (backoff/circuit breaker).",
            details=errors,
            rate_limited=any_rate_limited,
        )
        
        # Save state after all instances failed
        self.save_state()
        
        return response

    async def _try_instance(
        self, url: str, query: str, limit: int
    ) -> SearchResponse:
        """Try a single instance for a search query.

        Args:
            url: The instance URL.
            query: The search query.
            limit: Maximum results to return.

        Returns:
            SearchResponse with results or error.
        """
        # Build search URL
        search_url = f"{url.rstrip('/')}/search"
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(search_url, params=params)

            # Handle rate limiting (HTTP 429)
            if response.status_code == 429:
                return SearchResponse(
                    success=False,
                    query=query,
                    error="Rate limited (429)",
                    message="Instance is rate limiting requests",
                    rate_limited=True,
                )

            # Handle anti-bot protection (HTTP 418) and other client errors
            if response.status_code in (418, 403):
                return SearchResponse(
                    success=False,
                    query=query,
                    error=f"Access blocked ({response.status_code})",
                    message="Instance blocked the request (possible anti-bot protection)",
                    rate_limited=True,
                )

            # Handle server errors
            if response.status_code >= 500:
                return SearchResponse(
                    success=False,
                    query=query,
                    error=f"Server error ({response.status_code})",
                    message="Instance returned a server error",
                )

            # Raise for other HTTP errors (4xx except 418, 403, 429)
            response.raise_for_status()

            # Parse response
            data = response.json()

        # Extract results from SearXNG response format
        results: list[SearchResult] = []
        raw_results = data.get("results", [])

        for item in raw_results:
            result = SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                engine=item.get("engine", "unknown"),
                category=item.get("category", "general"),
            )
            results.append(result)

        # Detect implicit rate limiting: HTTP 200 with empty results
        # SearXNG returns empty results when rate limited instead of HTTP 429
        if len(results) == 0:
            return SearchResponse(
                success=False,
                query=query,
                error="Empty results (possible rate limiting)",
                message="Instance returned empty results. "
                "This typically indicates rate limiting or temporary unavailability.",
                rate_limited=True,
            )

        # Also check for answers (SearXNG can return answers alongside results)
        # Not adding to results list as they're typically summaries

        return SearchResponse(
            success=True,
            query=query,
            results=results,
            count=len(results),
        )

    def get_status_summary(self) -> dict:
        """Get a summary of all instance statuses.

        Returns:
            Dictionary with status counts and instance details.
        """
        closed = 0
        open_count = 0
        half_open = 0
        in_backoff = 0

        for status in self.instances.values():
            if status.state == CircuitState.CLOSED:
                closed += 1
            elif status.state == CircuitState.OPEN:
                open_count += 1
            else:
                half_open += 1
            
            if status.get_backoff_remaining():
                in_backoff += 1

        return {
            "total": len(self.instances),
            "closed": closed,
            "open": open_count,
            "half_open": half_open,
            "in_backoff": in_backoff,
            "available": len(self.instances) - open_count - in_backoff,
            "instances": [status.to_dict() for status in self.instances.values()],
        }

    def reset_instance(self, url: Optional[str] = None) -> dict:
        """Reset instance state.
        
        Args:
            url: Specific instance URL to reset, or None to reset all.
            
        Returns:
            Summary of reset action.
        """
        if url:
            if url in self.instances:
                self.instances[url].reset()
                self._mark_dirty()
                self.save_state()
                return {"reset": [url], "message": f"Reset {url}"}
            return {"reset": [], "message": f"Unknown instance: {url}"}
        else:
            count = len(self.instances)
            for status in self.instances.values():
                status.reset()
            self._mark_dirty()
            self.save_state()
            return {"reset": list(self.instances.keys()), "message": f"Reset all {count} instances"}

    def get_available_instances(self) -> list[dict]:
        """Get list of currently available instances.
        
        Returns:
            List of available instance info.
        """
        available = []
        for url, status in self.instances.items():
            if status.is_available():
                available.append({
                    "url": url,
                    "state": status.state.value,
                    "failure_count": status.failure_count,
                })
        return available
