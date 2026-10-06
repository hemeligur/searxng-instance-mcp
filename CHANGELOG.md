# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- httpx>=0.25.0
- tenacity>=8.0.0

### Bug Fixes
- Migrated from `mcp[cli]` to `fastmcp>=4.0.0` for compatibility with modern MCP protocol
