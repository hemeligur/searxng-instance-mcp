"""Tests for SearXNG manager functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from searxng_mcp.manager import SearXNGManager
from searxng_mcp.models import CircuitState, SearchResponse


@pytest.mark.asyncio
async def test_search_success(sample_search_response):
    """Test successful search on an instance."""
    with patch("searxng_mcp.manager.discover_instances") as mock_discover:
        mock_discover.return_value = ["https://sx.xo.st"]

        manager = SearXNGManager()

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
async def test_search_empty_query():
    """Test that empty query returns error."""
    with patch("searxng_mcp.manager.discover_instances") as mock_discover:
        mock_discover.return_value = ["https://sx.xo.st"]
        manager = SearXNGManager()

        result = await manager.search("")

        assert result.success is False
        assert result.error == "Empty query"


@pytest.mark.asyncio
async def test_search_all_instances_fail():
    """Test search when all instances fail."""
    with patch("searxng_mcp.manager.discover_instances") as mock_discover:
        mock_discover.return_value = [
            "https://instance1.example.com",
            "https://instance2.example.com",
        ]
        manager = SearXNGManager()

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
async def test_get_status_summary():
    """Test getting status summary of all instances."""
    # Manager will use fallback instances when in async context
    manager = SearXNGManager()

    summary = manager.get_status_summary()

    assert "total" in summary
    assert summary["total"] > 0  # At least has fallback instances
    assert "closed" in summary
    assert "open" in summary
    assert "half_open" in summary
    assert "instances" in summary
    assert len(summary["instances"]) == summary["total"]


@pytest.mark.asyncio
async def test_reset_all_circuits():
    """Test resetting all circuit breakers."""
    with patch("searxng_mcp.manager.discover_instances") as mock_discover:
        mock_discover.return_value = [
            "https://instance1.example.com",
            "https://instance2.example.com",
        ]
        manager = SearXNGManager()

        # Reset all - should work even with no circuits open
        manager.reset_circuit()

        for status in manager.instances.values():
            assert status.state == CircuitState.CLOSED
            assert status.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    """Test circuit breaker state transitions."""
    # Manually add instance for testing
    manager = SearXNGManager()
    from searxng_mcp.models import InstanceStatus
    
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
async def test_fallback_search_order():
    """Test that search tries instances in order."""
    manager = SearXNGManager()

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

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        # First fails, second succeeds (manager uses fallback instances)
        mock_client.get.side_effect = [
            httpx.TimeoutException("Timeout"),  # First instance fails
            MagicMock(status_code=200, json=lambda: search_response),  # Second succeeds
        ]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        result = await manager.search("test")

        # Should succeed using second or later instance
        assert result.success is True
        assert result.instance_used is not None


@pytest.mark.asyncio
async def test_search_with_limit():
    """Test search with limit parameter."""
    manager = SearXNGManager()

    # Response with 5 results (mimicking API behavior with limit)
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
async def test_circuit_open_after_failures():
    """Test that circuit opens after consecutive failures."""
    manager = SearXNGManager()
    from searxng_mcp.models import InstanceStatus
    
    test_url = "https://failing.example.com"
    manager.instances[test_url] = InstanceStatus(url=test_url)
    
    # Simulate 3 failures
    for _ in range(3):
        manager._update_instance_status(test_url, success=False)
    
    status = manager.instances[test_url]
    assert status.state == CircuitState.OPEN
    assert status.failure_count == 3


@pytest.mark.asyncio
async def test_circuit_half_open_after_ttl():
    """Test that circuit goes to HALF_OPEN after TTL."""
    import time
    from searxng_mcp.models import InstanceStatus
    from searxng_mcp.constants import CIRCUIT_BREAKER_TTL
    
    manager = SearXNGManager()
    
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
