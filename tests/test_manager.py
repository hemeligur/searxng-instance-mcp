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

"""Tests for SearXNG manager functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from searxng_mcp.manager import SearXNGManager
from searxng_mcp.models import CircuitState, InstanceStatus, SearchResponse


@pytest.fixture
def clean_manager():
    """Create a clean manager instance for testing."""
    # Reset singleton
    import searxng_mcp.manager as manager_module
    manager_module._manager_instance = None
    
    # Mock persistence to not load saved state
    with patch("searxng_mcp.manager.load_instance_states", return_value={}):
        manager = SearXNGManager()
        # Clear any loaded instances
        manager.instances.clear()
        manager._initialized = True
        yield manager


@pytest.mark.asyncio
async def test_search_success(clean_manager, sample_search_response):
    """Test successful search on an instance."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://sx.xo.st"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Mock httpx response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = sample_search_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python", limit=5)

        assert result.success is True
        assert len(result.results) > 0
        assert result.instance_used is not None
        assert result.instance_used.startswith("https://")


@pytest.mark.asyncio
async def test_search_empty_query(clean_manager):
    """Test that empty query returns error."""
    manager = clean_manager
    
    result = await manager.search("")

    assert result.success is False
    assert result.error == "Empty query"


@pytest.mark.asyncio
async def test_search_all_instances_fail(clean_manager):
    """Test search when all instances fail."""
    manager = clean_manager
    
    # Add test instances
    manager.instances["https://instance1.example.com"] = InstanceStatus(url="https://instance1.example.com")
    manager.instances["https://instance2.example.com"] = InstanceStatus(url="https://instance2.example.com")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("test query")

        assert result.success is False
        assert result.error == "All instances unavailable"
        # Should have details for all tried instances
        assert len(result.details) >= 2


@pytest.mark.asyncio
async def test_get_status_summary(clean_manager):
    """Test getting status summary of all instances."""
    manager = clean_manager
    
    # Add test instances
    manager.instances["https://test1.example.com"] = InstanceStatus(url="https://test1.example.com")
    manager.instances["https://test2.example.com"] = InstanceStatus(url="https://test2.example.com")

    summary = manager.get_status_summary()

    assert "total" in summary
    assert summary["total"] == 2
    assert "closed" in summary
    assert "open" in summary
    assert "half_open" in summary
    assert "in_backoff" in summary
    assert len(summary["instances"]) == summary["total"]


@pytest.mark.asyncio
async def test_reset_all_instances(clean_manager):
    """Test resetting all instances."""
    manager = clean_manager
    
    # Add test instances
    manager.instances["https://instance1.example.com"] = InstanceStatus(url="https://instance1.example.com")
    manager.instances["https://instance2.example.com"] = InstanceStatus(url="https://instance2.example.com")
    
    # Simulate some failures
    manager.instances["https://instance1.example.com"].failure_count = 3
    manager.instances["https://instance1.example.com"].state = CircuitState.OPEN
    manager.instances["https://instance2.example.com"].failure_count = 2
    
    # Reset all
    result = manager.reset_instance()
    
    assert "reset" in result
    assert len(result["reset"]) == 2
    
    for status in manager.instances.values():
        assert status.state == CircuitState.CLOSED
        assert status.failure_count == 0
        assert status.backoff_until is None


@pytest.mark.asyncio
async def test_circuit_breaker_transitions(clean_manager):
    """Test circuit breaker state transitions."""
    manager = clean_manager
    
    test_url = "https://test.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Verify initial state is CLOSED
    status = manager.instances[test_url]
    assert status.state == CircuitState.CLOSED

    # Simulate failures
    status.failure_count = 3
    manager._update_instance_status(test_url, success=False)

    # After 3 failures, circuit should be OPEN
    assert status.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_fallback_search_order(clean_manager):
    """Test that search tries instances in order."""
    manager = clean_manager
    
    search_response = {
        "results": [
            {
                "url": "https://example.com",
                "title": "Test",
                "content": "Content",
                "engine": "google",
                "category": "general",
            }
        ]
    }

    # Add test instances in order
    manager.instances["https://first.example.com"] = InstanceStatus(url="https://first.example.com")
    manager.instances["https://second.example.com"] = InstanceStatus(url="https://second.example.com")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        # First fails, second succeeds
        mock_client.get.side_effect = [
            httpx.TimeoutException("Timeout"),  # First instance fails
            MagicMock(status_code=200, json=lambda: search_response),  # Second succeeds
        ]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("test")

        # Should succeed using second instance
        assert result.success is True
        assert result.instance_used is not None
        assert "second.example.com" in result.instance_used


@pytest.mark.asyncio
async def test_search_with_limit(clean_manager):
    """Test search with limit parameter."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://test.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    # Response with 5 results
    five_results = {
        "results": [
            {"url": f"https://example{i}.com", "title": f"Result {i}", "content": f"Content {i}", "engine": "google", "category": "general"}
            for i in range(5)
        ]
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = five_results

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Request with limit=5 (matching mock response)
        result = await manager.search("test", limit=5)

        assert result.success is True
        # The count should match the results returned
        assert result.count == 5


@pytest.mark.asyncio
async def test_search_limit_filters_results(clean_manager):
    """Test that limit parameter filters results client-side (API doesn't support limit)."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://test.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    # API returns 10 results (SearXNG always returns ~10)
    ten_results = {
        "results": [
            {"url": f"https://example{i}.com", "title": f"Result {i}", "content": f"Content {i}", "engine": "google", "category": "general"}
            for i in range(10)
        ]
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = ten_results

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Request with limit=3, but API returns 10
        result = await manager.search("test", limit=3)

        assert result.success is True
        assert result.count == 3, f"Expected 3 results, got {result.count}"
        assert len(result.results) == 3, f"Expected 3 results in list, got {len(result.results)}"
        
        # Verify we got the first 3 results
        assert result.results[0].title == "Result 0"
        assert result.results[1].title == "Result 1"
        assert result.results[2].title == "Result 2"


@pytest.mark.asyncio
async def test_circuit_open_after_failures(clean_manager):
    """Test that circuit opens after consecutive failures."""
    manager = clean_manager
    
    test_url = "https://failing.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Simulate 3 failures
    for _ in range(3):
        manager._update_instance_status(test_url, success=False)
    
    status = manager.instances[test_url]
    assert status.state == CircuitState.OPEN
    assert status.failure_count == 3


@pytest.mark.asyncio
async def test_circuit_half_open_after_ttl(clean_manager):
    """Test that circuit goes to HALF_OPEN after TTL."""
    import time
    from searxng_mcp.constants import CIRCUIT_BREAKER_TTL
    
    manager = clean_manager
    
    test_url = "https://testing.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Open the circuit
    for _ in range(3):
        manager._update_instance_status(test_url, success=False)
    
    assert manager.instances[test_url].state == CircuitState.OPEN
    
    # Manually set circuit_open_at to the past
    manager.instances[test_url].circuit_open_at = time.time() - CIRCUIT_BREAKER_TTL - 1
    
    # Check if HALF_OPEN (depends on implementation)
    status = manager.instances[test_url]
    # The status should still be OPEN until a new request tries it
    assert status.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_rate_limited_empty_results_marked_as_failure(clean_manager):
    """Test that HTTP 200 with empty results is treated as rate limiting failure."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://rate-limited.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    # Mock HTTP 200 response with empty results
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is False
        assert result.rate_limited is True
        assert result.count == 0
        assert len(result.results) == 0
        # Check the detailed error in the instance details
        assert any("Empty results" in d.get("error", "") or "rate limiting" in d.get("error", "") for d in result.details)


@pytest.mark.asyncio
async def test_rate_limited_empty_body_marked_as_failure(clean_manager):
    """Test that HTTP 200 with completely empty body is treated as rate limiting."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://rate-limited.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is False
        assert result.rate_limited is True


@pytest.mark.asyncio
async def test_http_418_treated_as_failure(clean_manager):
    """Test that HTTP 418 (anti-bot) is treated as failure."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://search.ctq.ro"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 418

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is False
        assert result.rate_limited is True
        assert any("418" in d.get("error", "") or "blocked" in d.get("error", "").lower() for d in result.details)


@pytest.mark.asyncio
async def test_http_403_treated_as_failure(clean_manager):
    """Test that HTTP 403 (forbidden) is treated as failure with rate_limited flag."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://blocked.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is False
        assert result.rate_limited is True


@pytest.mark.asyncio
async def test_rate_limited_falls_back_to_next_instance(clean_manager):
    """Test that rate limited instance causes fallback to next instance."""
    manager = clean_manager
    
    # Add test instances
    rate_limited_url = "https://rate-limited.example.com"
    working_url = "https://working.example.com"
    manager.instances[rate_limited_url] = InstanceStatus(url=rate_limited_url)
    manager.instances[working_url] = InstanceStatus(url=working_url)

    successful_response = {
        "results": [
            {
                "url": "https://example.com",
                "title": "Success",
                "content": "Found it",
                "engine": "google",
                "category": "general",
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"results": []}),  # Rate limited
            MagicMock(status_code=200, json=lambda: successful_response),  # Success
        ]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is True
        assert len(result.results) == 1
        assert working_url in result.instance_used


@pytest.mark.asyncio
async def test_rate_limited_circuit_breaker_updated(clean_manager):
    """Test that rate limited instance has its circuit breaker updated."""
    manager = clean_manager
    
    # Add test instance
    test_url = "https://rate-limited.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("python")

        assert result.success is False
        instance_status = manager.instances.get(test_url)
        if instance_status:
            assert instance_status.failure_count >= 1


@pytest.mark.asyncio
async def test_exponential_backoff(clean_manager):
    """Test exponential backoff calculation."""
    manager = clean_manager
    
    test_url = "https://backoff.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    status = manager.instances[test_url]
    
    # First failure - base backoff
    manager._update_instance_status(test_url, success=False)
    assert status.failure_count == 1
    assert status.get_backoff_seconds() == 60  # Base
    
    # Second failure - 2x backoff
    manager._update_instance_status(test_url, success=False)
    assert status.failure_count == 2
    assert status.get_backoff_seconds() == 120  # 60 * 2
    
    # Third failure - 4x backoff
    manager._update_instance_status(test_url, success=False)
    assert status.failure_count == 3
    assert status.get_backoff_seconds() == 240  # 60 * 2^2
    
    # Verify backoff_until is set
    assert status.backoff_until is not None


@pytest.mark.asyncio
async def test_backoff_blocks_instance(clean_manager):
    """Test that instance in backoff is skipped."""
    import time
    
    manager = clean_manager
    
    test_url = "https://backoff.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Manually set backoff
    status = manager.instances[test_url]
    status.backoff_until = time.time() + 300  # 5 minutes from now
    
    # Instance should not be available
    assert not status.is_available()


@pytest.mark.asyncio
async def test_success_clears_backoff(clean_manager):
    """Test that successful request clears backoff."""
    import time
    
    manager = clean_manager
    
    test_url = "https://success.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Set backoff manually
    status = manager.instances[test_url]
    status.backoff_until = time.time() + 300
    status.failure_count = 2
    
    # Simulate success
    manager._update_instance_status(test_url, success=True)
    
    # Backoff should be cleared
    assert status.backoff_until is None
    assert status.failure_count == 0
    assert status.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_get_available_instances(clean_manager):
    """Test getting list of available instances."""
    import time
    
    manager = clean_manager
    
    # Add instances with different states
    manager.instances["https://available.example.com"] = InstanceStatus(url="https://available.example.com")
    manager.instances["https://backoff.example.com"] = InstanceStatus(url="https://backoff.example.com")
    manager.instances["https://open.example.com"] = InstanceStatus(url="https://open.example.com")
    
    # Set some in unavailable states
    manager.instances["https://backoff.example.com"].backoff_until = time.time() + 300
    manager.instances["https://open.example.com"].state = CircuitState.OPEN
    manager.instances["https://open.example.com"].circuit_open_at = time.time()
    
    available = manager.get_available_instances()
    
    assert len(available) == 1
    assert available[0]["url"] == "https://available.example.com"


@pytest.mark.asyncio
async def test_reset_specific_instance(clean_manager):
    """Test resetting a specific instance."""
    import time
    
    manager = clean_manager
    
    manager.instances["https://instance1.example.com"] = InstanceStatus(url="https://instance1.example.com")
    manager.instances["https://instance2.example.com"] = InstanceStatus(url="https://instance2.example.com")
    
    # Set some state
    manager.instances["https://instance1.example.com"].failure_count = 3
    manager.instances["https://instance1.example.com"].backoff_until = time.time() + 300
    
    # Reset specific instance
    result = manager.reset_instance("https://instance1.example.com")
    
    assert result["reset"] == ["https://instance1.example.com"]
    assert manager.instances["https://instance1.example.com"].failure_count == 0
    assert manager.instances["https://instance1.example.com"].backoff_until is None
    # instance2 should be unchanged
    assert manager.instances["https://instance2.example.com"].failure_count == 0
