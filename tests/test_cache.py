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

"""Tests for caching functionality."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from searxng_mcp.discovery import (
    discover_instances,
    _load_cached_instances,
    _save_instances_to_cache,
    clear_cache,
    get_cache_info,
)


@pytest.mark.asyncio
async def test_cache_works(temp_cache_dir):
    """Test that cache is used when available."""
    # Create cache with known instances
    cached_instances = ["https://cached1.example.com", "https://cached2.example.com"]
    _save_instances_to_cache(cached_instances)

    # Discover instances (should use cache)
    instances = await discover_instances(use_cache=True)

    assert instances == cached_instances


@pytest.mark.asyncio
async def test_cache_bypassed_when_use_cache_false(
    temp_cache_dir, sample_instances_api_response
):
    """Test that cache is bypassed when use_cache=False."""
    # Create stale cache
    _save_instances_to_cache(["https://cached.example.com"])

    # Mock API response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = sample_instances_api_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get.return_value.__aenter__.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Discover with use_cache=False should fetch from API
        instances = await discover_instances(use_cache=False)

    assert "https://sx.xo.st" in instances
    assert "https://cached.example.com" not in instances


def test_cache_expiry(temp_cache_dir, monkeypatch):
    """Test that expired cache is not used."""
    from searxng_mcp import discovery

    # Create cache with old timestamp (simulate expiry)
    cache_data = {
        "timestamp": time.time() - 7200,   # 2 hours ago
        "instances": ["https://old.example.com"],
    }

    with open(discovery.CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

    # Load should return None due to expiry
    cached = _load_cached_instances()
    assert cached is None


def test_cache_preserves_order(temp_cache_dir):
    """Test that cache preserves instance order."""
    ordered_instances = [
        "https://first.example.com",
        "https://second.example.com",
        "https://third.example.com",
    ]

    _save_instances_to_cache(ordered_instances)
    loaded = _load_cached_instances()

    assert loaded == ordered_instances


def test_cache_handles_corrupted_file(temp_cache_dir):
    """Test that corrupted cache file is handled gracefully."""
    from searxng_mcp import discovery

    # Write invalid JSON
    with open(discovery.CACHE_FILE, "w") as f:
        f.write("not valid json{")

    # Should return None instead of crashing
    cached = _load_cached_instances()
    assert cached is None


def test_cache_info_shows_count(temp_cache_dir):
    """Test that cache info shows correct instance count."""
    instances = [
        "https://a.example.com",
        "https://b.example.com",
        "https://c.example.com",
    ]
    _save_instances_to_cache(instances)

    info = get_cache_info()

    assert info is not None
    assert info["instance_count"] == 3


@pytest.mark.asyncio
async def test_cache_updated_after_discovery(
    temp_cache_dir, sample_instances_api_response
):
    """Test that cache is updated after successful discovery."""
    from searxng_mcp import discovery

    # Ensure no cache initially
    clear_cache()
    assert get_cache_info() is None

    # Mock API response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = sample_instances_api_response

    # Create async mock for the response
    async def mock_get(*args, **kwargs):
        return mock_response
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await discover_instances(use_cache=False)

    # Cache should now exist
    info = get_cache_info()
    assert info is not None
    assert info["instance_count"] == 3
