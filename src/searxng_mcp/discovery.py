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

"""Instance discovery for SearXNG MCP server.

Discovers and caches available SearXNG instances from searx.space.
"""

import json
import logging
import os
import time
from pathlib import Path

import httpx

from .models import DiscoveredInstance

logger = logging.getLogger(__name__)

# Configuration
SEARX_SPACE_API = "https://searx.space/api/v1/instances"
DEFAULT_CACHE_TTL = int(os.environ.get("SEARXNG_CACHE_TTL", "3600"))  # 1 hour default

# Fallback instances (hardcoded reliable instances)
FALLBACK_INSTANCES = [
    "https://sx.xo.st",
    "https://search.ctq.ro",
    "https://xka.cz",
]

# Cache paths
CACHE_DIR = Path.home() / ".cache" / "searxng-mcp"
CACHE_FILE = CACHE_DIR / "instances.json"

# Required engines for a healthy instance
REQUIRED_ENGINES = {"google", "bing", "duckduckgo"}

# Filter criteria
MIN_UPTIME = 95.0
VALID_TLS_RANKS = {"A+", "A"}
MAX_INSTANCES = 20


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_cached_instances() -> list[str] | None:
    """Load instances from cache if valid.

    Returns:
        List of instance URLs if cache exists and is valid, None otherwise.
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        timestamp = data.get("timestamp", 0)
        instances = data.get("instances", [])

        # Check if cache is still valid
        if time.time() - timestamp < DEFAULT_CACHE_TTL:
            logger.debug(f"Cache valid, {len(instances)} instances")
            return instances

        logger.debug("Cache expired")
        return None

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_instances_to_cache(instances: list[str]) -> None:
    """Save instances to cache file.

    Args:
        instances: List of instance URLs to cache.
    """
    _ensure_cache_dir()

    data = {
        "timestamp": time.time(),
        "instances": instances,
    }

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Cached {len(instances)} instances")
    except IOError as e:
        logger.warning(f"Failed to save cache: {e}")


async def _fetch_instances_from_api() -> list[str]:
    """Fetch instances from searx.space API.

    Returns:
        List of instance URLs from the API.

    Raises:
        httpx.HTTPError: If the API request fails.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(SEARX_SPACE_API)
        response.raise_for_status()

        data = response.json()

    # Parse instances from API response
    instances_data = data.get("instances", {})
    discovered: list[DiscoveredInstance] = []

    for instance_data in instances_data.values():
        try:
            instance = DiscoveredInstance.from_api_response(instance_data)
            discovered.append(instance)
        except Exception as e:
            logger.debug(f"Failed to parse instance: {e}")
            continue

    # Filter instances by quality criteria
    filtered_instances: list[DiscoveredInstance] = []

    for instance in discovered:
        # Check uptime threshold
        if instance.uptime < MIN_UPTIME:
            continue

        # Check TLS rank
        if instance.tls_rank not in VALID_TLS_RANKS:
            continue

        # Check required engines
        instance_engines = set(engine.lower() for engine in instance.engines)
        if not REQUIRED_ENGINES.issubset(instance_engines):
            continue

        # Instance passes all filters
        filtered_instances.append(instance)

    # Sort by uptime (highest first) and limit
    filtered_instances.sort(key=lambda x: x.uptime, reverse=True)
    filtered_instances = filtered_instances[:MAX_INSTANCES]

    # Extract URLs
    instance_urls = [inst.url for inst in filtered_instances]

    logger.info(f"Discovered {len(instance_urls)} healthy instances from API")

    return instance_urls


async def discover_instances(use_cache: bool = True) -> list[str]:
    """Discover available SearXNG instances.

    Attempts to fetch instances from the searx.space API and filters them
    by quality criteria (uptime > 95%, TLS rank A+ or A, required engines).
    Results are cached locally.

    Args:
        use_cache: Whether to use cached instances if available. Defaults to True.

    Returns:
        List of URLs for available SearXNG instances.
    """
    # Try cache first
    if use_cache:
        cached = _load_cached_instances()
        if cached is not None:
            return cached

    # Fetch from API
    try:
        instances = await _fetch_instances_from_api()
        _save_instances_to_cache(instances)
        return instances

    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch instances from API: {e}")

    except Exception as e:
        logger.error(f"Unexpected error fetching instances: {e}")

    # Fallback to hardcoded instances
    logger.info("Using fallback instances")
    return list(FALLBACK_INSTANCES)


def get_fallback_instances() -> list[str]:
    """Get the list of fallback instances.

    Returns:
        List of fallback instance URLs.
    """
    return list(FALLBACK_INSTANCES)


def clear_cache() -> bool:
    """Clear the instance cache.

    Returns:
        True if cache was cleared successfully, False otherwise.
    """
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
            logger.info("Cache cleared")
            return True
        except IOError as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    return True


def get_cache_info() -> dict | None:
    """Get information about the current cache.

    Returns:
        Dictionary with cache info (timestamp, instance_count) or None if no cache.
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "timestamp": data.get("timestamp", 0),
            "instance_count": len(data.get("instances", [])),
            "ttl_seconds": DEFAULT_CACHE_TTL,
            "cache_file": str(CACHE_FILE),
        }
    except (json.JSONDecodeError, IOError):
        return None
