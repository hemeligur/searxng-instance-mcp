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

"""Tests for instance discovery functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from searxng_mcp.discovery import (
    discover_instances,
    get_fallback_instances,
    clear_cache,
    get_cache_info,
    _save_instances_to_cache,
    _load_cached_instances,
    FALLBACK_INSTANCES,
)
from searxng_mcp.models import DiscoveredInstance


@pytest.mark.asyncio
async def test_discover_instances_api_success(
    sample_instances_api_response, mock_httpx_client
):
    """Test discovering instances from API successfully."""
    # Setup mock
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = sample_instances_api_response
    mock_httpx_client.get.return_value = mock_response

    # Discover instances
    instances = await discover_instances(use_cache=False)

    # Verify results
    assert isinstance(instances, list)
    assert len(instances) == 3
    assert all(url.startswith("https://") for url in instances)


@pytest.mark.asyncio
async def test_discover_instances_filters_by_uptime(mock_httpx_client):
    """Test that instances with low uptime are filtered out."""
    # New format: URL is the key, data is in the value, uptime is at root level
    response_data = {
        "instances": {
            "https://high-uptime.example.com": {
                "uptime": {"uptimeDay": 99.0},
                "tls": {"grade": "A+"},
                "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
                "alternativeUrls": {},
            },
            "https://low-uptime.example.com": {
                "uptime": {"uptimeDay": 50.0},
                "tls": {"grade": "A+"},
                "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
                "alternativeUrls": {},
            },
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_httpx_client.get.return_value = mock_response

    instances = await discover_instances(use_cache=False)

    assert len(instances) == 1
    assert "https://high-uptime.example.com" in instances


@pytest.mark.asyncio
async def test_discover_instances_filters_by_tls_rank(mock_httpx_client):
    """Test that instances with poor TLS rank are filtered out."""
    response_data = {
        "instances": {
            "https://good-tls.example.com": {
                "uptime": {"uptimeDay": 99.0},
                "tls": {"grade": "A+"},
                "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
                "alternativeUrls": {},
            },
            "https://bad-tls.example.com": {
                "uptime": {"uptimeDay": 99.0},
                "tls": {"grade": "C"},
                "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
                "alternativeUrls": {},
            },
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_httpx_client.get.return_value = mock_response

    instances = await discover_instances(use_cache=False)

    assert len(instances) == 1
    assert "https://good-tls.example.com" in instances


@pytest.mark.asyncio
async def test_discover_instances_filters_missing_engines(mock_httpx_client):
    """Test that instances missing required engines are filtered out."""
    response_data = {
        "instances": {
            "https://complete.example.com": {
                "uptime": {"uptimeDay": 99.0},
                "tls": {"grade": "A+"},
                "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
                "alternativeUrls": {},
            },
            "https://missing-engine.example.com": {
                "uptime": {"uptimeDay": 99.0},
                "tls": {"grade": "A+"},
                "engines": {"google": {}},  # Missing bing and duckduckgo
                "alternativeUrls": {},
            },
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_httpx_client.get.return_value = mock_response

    instances = await discover_instances(use_cache=False)

    assert len(instances) == 1
    assert "https://complete.example.com" in instances


@pytest.mark.asyncio
async def test_discover_instances_api_failure_uses_fallback(mock_httpx_client):
    """Test that API failure falls back to hardcoded instances."""
    # Make API call fail
    mock_httpx_client.get.side_effect = httpx.HTTPError("API Error")

    instances = await discover_instances(use_cache=False)

    # Should return fallback instances
    assert isinstance(instances, list)
    assert len(instances) > 0
    assert instances == FALLBACK_INSTANCES


@pytest.mark.asyncio
async def test_discover_instances_github_fallback(mock_httpx_client):
    """Test that GitHub active instances are used as fallback."""
    # First call (searx.space) raises HTTPError
    async def raise_error(*args, **kwargs):
        raise httpx.HTTPError("searx.space error")

    mock_httpx_client.get.side_effect = raise_error

    # Now patch the GitHub fallback function directly
    from searxng_mcp import discovery

    original_github = discovery._fetch_github_active_instances

    async def mock_github():
        return [
            "https://github-instance-1.example.com",
            "https://github-instance-2.example.com",
        ]

    discovery._fetch_github_active_instances = mock_github

    try:
        instances = await discover_instances(use_cache=False)

        assert len(instances) == 2
        assert "https://github-instance-1.example.com" in instances
        assert "https://github-instance-2.example.com" in instances
    finally:
        discovery._fetch_github_active_instances = original_github


def test_fallback_instances_count():
    """Test that fallback instances list has at least 10 instances."""
    instances = get_fallback_instances()

    assert len(instances) >= 10, f"Expected >= 10 fallback instances, got {len(instances)}"


def test_fallback_instances_all_valid():
    """Test that all fallback instances are valid URLs."""
    instances = get_fallback_instances()

    for url in instances:
        assert url.startswith("https://"), f"Invalid URL format: {url}"


def test_get_fallback_instances():
    """Test getting fallback instances."""
    instances = get_fallback_instances()

    assert isinstance(instances, list)
    assert len(instances) > 0
    assert all(isinstance(url, str) for url in instances)
    assert all(url.startswith("https://") for url in instances)


def test_save_and_load_cached_instances(temp_cache_dir):
    """Test saving and loading instances from cache."""
    test_instances = [
        "https://instance1.example.com",
        "https://instance2.example.com",
    ]

    # Save to cache
    _save_instances_to_cache(test_instances)

    # Load from cache
    cached = _load_cached_instances()

    assert cached is not None
    assert cached == test_instances


def test_clear_cache(temp_cache_dir):
    """Test clearing the cache."""
    # First save something to cache
    _save_instances_to_cache(["https://example.com"])

    # Verify cache exists
    assert _load_cached_instances() is not None

    # Clear cache
    result = clear_cache()

    # Verify cache is cleared
    assert result is True
    assert _load_cached_instances() is None


def test_get_cache_info_no_cache(temp_cache_dir):
    """Test getting cache info when no cache exists."""
    info = get_cache_info()
    assert info is None


def test_get_cache_info_with_cache(temp_cache_dir):
    """Test getting cache info when cache exists."""
    # Create cache
    _save_instances_to_cache(["https://example.com"])

    info = get_cache_info()

    assert info is not None
    assert "timestamp" in info
    assert "instance_count" in info
    assert info["instance_count"] == 1
