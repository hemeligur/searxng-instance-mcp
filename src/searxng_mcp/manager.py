"""SearXNG Manager - Pool management and search execution with circuit breaker."""

import logging
from typing import Optional

import httpx

from .constants import DEFAULT_LIMIT, DEFAULT_TIMEOUT
from .discovery import discover_instances, get_fallback_instances
from .models import CircuitState, InstanceStatus, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearXNGManager:
    """Manages a pool of SearXNG instances with circuit breaker pattern.

    Features:
    - Automatic instance discovery from searx.space
    - Circuit breaker with CLOSED → OPEN → HALF_OPEN states
    - 5-minute TTL for OPEN → HALF_OPEN transition
    - Automatic fallback to hardcoded instances
    """

    def __init__(self) -> None:
        """Initialize the SearXNG manager."""
        self.instances: dict[str, InstanceStatus] = {}
        self._initialize_instances()

    def _initialize_instances(self) -> None:
        """Initialize instances from discovery or fallback.

        Populates the instance pool with URLs from discovery
        or falls back to hardcoded instances if discovery fails.
        """
        try:
            import asyncio
            
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context - defer to sync fallback
            logger.warning("Cannot use async discovery from async context, using fallback")
            self._load_fallback_instances()
        except RuntimeError:
            # No running event loop - safe to use asyncio.run()
            try:
                instances = asyncio.run(discover_instances(use_cache=True))
                for url in instances:
                    self.instances[url] = InstanceStatus(url=url)
                logger.info(f"Loaded {len(instances)} instances from discovery")
            except Exception as e:
                logger.warning(f"Failed to discover instances: {e}, using fallback")
                self._load_fallback_instances()

    def _load_fallback_instances(self) -> None:
        """Load fallback instances."""
        fallback_urls = get_fallback_instances()
        for url in fallback_urls:
            self.instances[url] = InstanceStatus(url=url)
        logger.info(f"Loaded {len(fallback_urls)} fallback instances")

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
            logger.debug(
                f"Instance {url}: failure ({error}), "
                f"state={status.state.value}, failures={status.failure_count}"
            )

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

        for url, status in self.instances.items():
            # Skip if circuit is OPEN and TTL hasn't expired
            if not status.is_available():
                logger.debug(f"Skipping {url}: circuit {status.state.value}")
                continue

            # Attempt search on this instance
            try:
                result = await self._try_instance(url, query, limit)
                if result.success:
                    result.instance_used = url
                    self._update_instance_status(url, success=True)
                    return result
                else:
                    errors.append({"instance": url, "error": result.error})
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

        return SearchResponse(
            success=False,
            query=query,
            error="All instances unavailable",
            message="Failed to search using any available instance. "
            "All instances may be experiencing issues.",
            details=errors,
        )

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

            # Handle rate limiting
            if response.status_code == 429:
                return SearchResponse(
                    success=False,
                    query=query,
                    error="Rate limited (429)",
                    message="Instance is rate limiting requests",
                )

            # Handle server errors
            if response.status_code >= 500:
                return SearchResponse(
                    success=False,
                    query=query,
                    error=f"Server error ({response.status_code})",
                    message="Instance returned a server error",
                )

            # Raise for other HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

        # Extract results from SearXNG response format
        results: list[SearchResult] = []

        for item in data.get("results", []):
            result = SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                engine=item.get("engine", "unknown"),
                category=item.get("category", "general"),
            )
            results.append(result)

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

        for status in self.instances.values():
            if status.state == CircuitState.CLOSED:
                closed += 1
            elif status.state == CircuitState.OPEN:
                open_count += 1
            else:
                half_open += 1

        return {
            "total": len(self.instances),
            "closed": closed,
            "open": open_count,
            "half_open": half_open,
            "instances": [
                {
                    "url": status.url,
                    "state": status.state.value,
                    "failure_count": status.failure_count,
                    "last_failure": status.last_failure,
                    "last_success": status.last_success,
                }
                for status in self.instances.values()
            ],
        }

    def reset_circuit(self, url: Optional[str] = None) -> None:
        """Reset circuit breaker for an instance or all instances.

        Args:
            url: Specific instance URL to reset, or None to reset all.
        """
        if url:
            if url in self.instances:
                self.instances[url].state = CircuitState.CLOSED
                self.instances[url].failure_count = 0
                self.instances[url].circuit_open_at = None
                logger.info(f"Reset circuit for {url}")
        else:
            for status in self.instances.values():
                status.state = CircuitState.CLOSED
                status.failure_count = 0
                status.circuit_open_at = None
            logger.info("Reset all circuits")
