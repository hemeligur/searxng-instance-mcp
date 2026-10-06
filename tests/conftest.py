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

"""Pytest configuration and fixtures for searxng-mcp tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response for testing."""

    def _create_response(
        status_code: int = 200,
        json_data: dict | None = None,
    ) -> httpx.Response:
        """Create a mock response with the given data."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.raise_for_status = MagicMock()
        if status_code >= 400:
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=response,
            )
        return response

    return _create_response


@pytest.fixture
def sample_search_response() -> dict:
    """Sample successful search response from SearXNG API."""
    return {
        "results": [
            {
                "url": "https://example.com/python",
                "title": "Python Programming Language",
                "content": "Python is a high-level programming language.",
                "engine": "google",
                "category": "it",
            },
            {
                "url": "https://example.com/python-docs",
                "title": "Python Documentation",
                "content": "Official Python documentation and guides.",
                "engine": "bing",
                "category": "it",
            },
        ],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
        "responses": [],
    }


@pytest.fixture
def sample_instances_api_response() -> dict:
    """Sample response from searx.space API."""
    return {
        "instances": {
            "sx.xo.st": {
                "name": "sx.xo.st",
                "url": "https://sx.xo.st",
                "network": {
                    "uptime": 100,
                    "tls_rank": "A+",
                },
                "engines": ["google", "bing", "duckduckgo"],
            },
            "searxng.org": {
                "name": "searxng.org",
                "url": "https://searxng.org",
                "network": {
                    "uptime": 98,
                    "tls_rank": "A",
                },
                "engines": ["google", "bing", "duckduckgo"],
            },
            "xka.cz": {
                "name": "xka.cz",
                "url": "https://xka.cz",
                "network": {
                    "uptime": 95,
                    "tls_rank": "A+",
                },
                "engines": ["google", "bing", "duckduckgo"],
            },
        }
    }


@pytest.fixture
def mock_httpx_client():
    """Create a mock AsyncClient for httpx."""
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        mock.return_value.__aexit__.return_value = None
        yield client_instance


@pytest.fixture
def temp_cache_dir(tmp_path, monkeypatch):
    """Create a temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("searxng_mcp.discovery.CACHE_DIR", cache_dir)
    monkeypatch.setattr("searxng_mcp.discovery.CACHE_FILE", cache_dir / "instances.json")
    return cache_dir
