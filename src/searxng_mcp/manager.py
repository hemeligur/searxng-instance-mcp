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
import time
from typing import Optional

import httpx

from .constants import DEFAULT_LIMIT, DEFAULT_TIMEOUT, get_disabled_instances, get_backoff_base, get_backoff_max, get_global_timeout
from .discovery import discover_instances, discover_instances_full, get_fallback_instances
from .models import CircuitState, InstanceStatus, SearchResponse, SearchResult, ExternalMetrics
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
    - Exponential backoff (60s base, 15min max, configurable via env)
    - Persistent state across server restarts
    - Random instance selection for load distribution
    - Automatic fallback to hardcoded instances
    - Support for disabled instances via SEARXNG_DISABLED_INSTANCES env var
    """

    def __init__(self) -> None:
        """Initialize the SearXNG manager."""
        self.instances: dict[str, InstanceStatus] = {}
        self._initialized = False
        self._dirty = False  # Track if state needs to be saved
        
        # Load persisted state
        self._load_persisted_state()
        
        # Apply disabled instances from config
        self._apply_disabled_instances()
    
    def _apply_disabled_instances(self) -> None:
        """Apply disabled instances from SEARXNG_DISABLED_INSTANCES env var."""
        disabled_urls = get_disabled_instances()
        for url in disabled_urls:
            if url in self.instances:
                self.instances[url].disabled = True
                logger.info(f"Instance disabled by config: {url}")

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
        
        # Get disabled instances from config
        disabled_urls = get_disabled_instances()
        
        try:
            # Fetch full instance data with metrics from searx.space
            discovered_instances = await discover_instances_full(use_cache=True)
            
            # Apply external metrics to instances
            metrics_applied = 0
            for discovered in discovered_instances:
                url = discovered.url
                
                # Create InstanceStatus if not exists
                if url not in self.instances:
                    status = InstanceStatus(url=url)
                    if url in disabled_urls:
                        status.disabled = True
                    self.instances[url] = status
                
                # Update external metrics
                external = ExternalMetrics(
                    uptime_day=discovered.uptime,
                    uptime_week=discovered.uptime_week,
                    tls_grade=discovered.tls_rank,
                    engine_count=len(discovered.engines),
                    error_load=discovered.error_load,
                    error_check=discovered.error_check,
                    network_country=discovered.network_country,
                )
                self.instances[url].update_external_metrics(external)
                metrics_applied += 1
                self._mark_dirty()
            
            # If no full data, try basic discovery
            if not discovered_instances:
                instances = await discover_instances(use_cache=True)
                for url in instances:
                    if url not in self.instances:
                        status = InstanceStatus(url=url)
                        if url in disabled_urls:
                            status.disabled = True
                        self.instances[url] = status
                    self._mark_dirty()
            
            # Shuffle for load distribution
            self._shuffle_instances()
            
            disabled_count = sum(1 for s in self.instances.values() if s.disabled)
            with_metrics = sum(1 for s in self.instances.values() if s._external_metrics is not None)
            logger.info(f"Initialized with {len(self.instances)} instances ({disabled_count} disabled, {with_metrics} with external metrics)")
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
    
    def _get_instances_by_tier(self) -> dict[int, list[tuple[str, "InstanceStatus"]]]:
        """Get instances organized by tier.
        
        Returns:
            Dict with tier numbers (1, 2, 3) as keys and lists of (url, status) tuples as values.
            Each tier list is shuffled for load distribution.
        """
        tiers: dict[int, list[tuple[str, InstanceStatus]]] = {1: [], 2: [], 3: []}
        
        for url, status in self.instances.items():
            # Only include available instances
            if status.is_available():
                tier = status.get_tier()
                tiers[tier].append((url, status))
        
        # Shuffle within each tier for load distribution
        for tier_urls in tiers.values():
            random.shuffle(tier_urls)
        
        return tiers

    async def _load_fallback_instances_async(self) -> None:
        """Load fallback instances asynchronously."""
        disabled_urls = get_disabled_instances()
        fallback_urls = get_fallback_instances()
        for url in fallback_urls:
            if url not in self.instances:
                status = InstanceStatus(url=url)
                # Mark as disabled if in config
                if url in disabled_urls:
                    status.disabled = True
                self.instances[url] = status
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

        Tries instances in tier order (T1 → T2 → T3), with circuit breaker pattern:
        - CLOSED: Normal operation, requests allowed
        - OPEN: After 3 failures, requests blocked until TTL expires
        - HALF_OPEN: After TTL, allows one test request

        Instances are organized by tier based on hybrid scoring:
        - T1 (Premium): score >= 0.70 - tried first
        - T2 (Standard): score >= 0.45 - fallback
        - T3 (Risky): score < 0.45 - last resort

        A global timeout (configurable via SEARXNG_GLOBAL_TIMEOUT env var, default 60s)
        prevents the search from taking too long when many instances are failing.

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

        # Get global timeout
        global_timeout = get_global_timeout()
        search_start_time = time.time()

        # Get instances organized by tier
        tiers = self._get_instances_by_tier()
        tier_counts = {t: len(instances) for t, instances in tiers.items()}
        logger.debug(f"Instance tiers: T1={tier_counts[1]}, T2={tier_counts[2]}, T3={tier_counts[3]}")

        # Try each available instance in tier order: T1 → T2 → T3
        errors: list[dict] = []
        skipped: list[str] = []

        for tier in [1, 2, 3]:
            for url, status in tiers[tier]:
                # Check global timeout
                elapsed = time.time() - search_start_time
                if elapsed >= global_timeout:
                    logger.warning(f"Global timeout reached ({global_timeout}s), stopping search")
                    break

                # Attempt search on this instance
                try:
                    start_time = time.time()
                    result = await self._try_instance(url, query, limit)
                    response_time = (time.time() - start_time) * 1000  # ms
                    
                    if result.success:
                        result.instance_used = url
                        # Update circuit breaker status
                        self._update_instance_status(url, success=True)
                        # Record request metrics for scoring
                        status.record_request(success=True, response_time_ms=response_time)
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
                        status.record_request(success=False)

                except httpx.TimeoutException:
                    error_msg = "Request timeout"
                    errors.append({"instance": url, "error": error_msg})
                    self._update_instance_status(url, success=False, error=error_msg)
                    status.record_request(success=False)
                    logger.warning(f"Timeout on {url}")

                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP {e.response.status_code}"
                    errors.append({"instance": url, "error": error_msg})
                    self._update_instance_status(url, success=False, error=error_msg)
                    status.record_request(success=False)
                    logger.warning(f"HTTP error on {url}: {e.response.status_code}")

                except httpx.RequestError as e:
                    error_msg = f"Request error: {type(e).__name__}"
                    errors.append({"instance": url, "error": error_msg})
                    self._update_instance_status(url, success=False, error=error_msg)
                    status.record_request(success=False)
                    logger.warning(f"Request error on {url}: {e}")

                except Exception as e:
                    error_msg = f"Unexpected error: {type(e).__name__}"
                    errors.append({"instance": url, "error": error_msg})
                    self._update_instance_status(url, success=False, error=error_msg)
                    status.record_request(success=False)
                    logger.error(f"Unexpected error on {url}: {e}")
            
            # Check if we hit global timeout after each tier
            elapsed = time.time() - search_start_time
            if elapsed >= global_timeout:
                break

        # Check if we hit global timeout
        elapsed = time.time() - search_start_time
        hit_timeout = elapsed >= global_timeout
        
        # Build error message
        if hit_timeout:
            error_msg = f"Global timeout ({global_timeout}s)"
            message = f"Search stopped after {elapsed:.1f}s (global timeout: {global_timeout}s). "
            message += f"Tried {len(errors)} instances before timeout."
        else:
            error_msg = "All instances unavailable"
            message = f"Failed to search using any available instance."

        # Check if any instance was rate limited
        any_rate_limited = any(
            isinstance(e, dict) and e.get("rate_limited") for e in errors
        )

        # Build response with skipped info
        response = SearchResponse(
            success=False,
            query=query,
            error=error_msg,
            message=message,
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
        # Note: SearXNG API does not support 'limit' parameter
        # Results are filtered client-side after receiving ~10 results
        params = {
            "q": query,
            "format": "json",
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

        # Limit results client-side (API doesn't support 'limit' parameter)
        results = results[:limit]

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
