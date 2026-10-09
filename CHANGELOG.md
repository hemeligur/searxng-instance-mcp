# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Issue #3 - `results_limit` parameter**: The `results_limit` parameter is now properly respected. The SearXNG API does not support a `limit` parameter, so the MCP now filters results client-side after receiving ~10 results from the API. Added `test_search_limit_filters_results` test.

## [0.2.0] - 2025-10-07

### Added
- **Rate limiting detection**: Automatically detects when instances return empty results due to rate limiting (HTTP 200, 418, or 403)
- **Environment variables for instance management**:
  - `SEARXNG_DISABLED_INSTANCES` - Comma-separated list of instance URLs to skip
  - `SEARXNG_DEBUG_TOOLS` - Enable/disable debug tools
  - `SEARXNG_BACKOFF_BASE` and `SEARXNG_BACKOFF_MAX` - Configure backoff timing
- **Debug tools**: `get_status`, `reset_circuit`, `clear_results_cache`
- **State persistence**: Circuit breaker state survives server restarts
- **RFC-001**: Instance quality tiers system (high/medium/low priority)
- **Enhanced fallback instances**: Improved discovery endpoint and expanded fallback list

### Fixed
- Discovery endpoint URL corrected
- Rate limiting detection when SearXNG returns empty results

### Tests
- 57 unit tests (increased from 27)
- New tests for rate limiting detection and backoff behavior

## [0.1.0] - 2025-10-06

### Added
- MCP server implementation using FastMCP
- Web search tool with automatic instance fallback
- Dynamic instance discovery from searx.space
- Circuit breaker pattern for instance health management
- Local cache for discovered instances
- 27 unit tests covering discovery, manager, and cache functionality

### Features
- 🔍 **Web Search**: Searches using SearXNG meta-search engine
- 🔄 **Fallback**: Automatic fallback to next instance when one fails
- 🛡️ **Circuit Breaker**: Prevents repeated calls to failing instances
- 🌐 **Discovery**: Dynamically discovers healthy instances
- 💾 **Cache**: Fast startup with cached instance list

### Architecture
- `server.py`: FastMCP server with `web_search` tool
- `manager.py`: Instance pool with circuit breaker
- `discovery.py`: Instance discovery from searx.space API
- `models.py`: Data models (CircuitState, SearchResult, etc.)
- `constants.py`: Configuration constants

### Dependencies
- fastmcp>=4.0.0
- httpx>=0.27.0
- tenacity>=8.0.0
- pydantic>=2.0.0
