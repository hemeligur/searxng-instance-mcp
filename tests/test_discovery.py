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
    response_data = {
        "instances": {
            "high-uptime": {
                "name": "high-uptime",
                "url": "https://high-uptime.example.com",
                "network": {"uptime": 99, "tls_rank": "A+"},
                "engines": ["google", "bing", "duckduckgo"],
            },
            "low-uptime": {
                "name": "low-uptime",
                "url": "https://low-uptime.example.com",
                "network": {"uptime": 50, "tls_rank": "A+"},
                "engines": ["google", "bing", "duckduckgo"],
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
            "good-tls": {
                "name": "good-tls",
                "url": "https://good-tls.example.com",
                "network": {"uptime": 99, "tls_rank": "A+"},
                "engines": ["google", "bing", "duckduckgo"],
            },
            "bad-tls": {
                "name": "bad-tls",
                "url": "https://bad-tls.example.com",
                "network": {"uptime": 99, "tls_rank": "C"},
                "engines": ["google", "bing", "duckduckgo"],
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
            "complete": {
                "name": "complete",
                "url": "https://complete.example.com",
                "network": {"uptime": 99, "tls_rank": "A+"},
                "engines": ["google", "bing", "duckduckgo"],
            },
            "missing-engine": {
                "name": "missing-engine",
                "url": "https://missing-engine.example.com",
                "network": {"uptime": 99, "tls_rank": "A+"},
                "engines": ["google"],  # Missing bing and duckduckgo
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
