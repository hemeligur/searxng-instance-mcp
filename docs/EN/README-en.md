# SearXNG Instance MCP

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![🇧🇷 Português](../../README.md)](../../README.md)

**MCP Client for Web Search via SearXNG** — connects to public online instances with automatic fallback.

> ⚠️ **Note**: This project is a **client** that connects to public/online SearXNG instances (like `sx.xo.st`, `search.ctq.ro`). If you want to run your own SearXNG instance locally, see [searxng-local-en.md](./searxng-local-en.md).

---

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────────────┐
│   Client    │────▶│  SearXNG MCP     │────▶│  Public Online Instances   │
│   (Pi/AI)   │◀────│  (this project)  │◀────│                             │
└─────────────┘     └──────────────────┘     │  • sx.xo.st                │
                           │                 │  • search.ctq.ro           │
                           │                 │  • searx.space (discovery) │
                           ▼                 └─────────────────────────────┘
                    ┌──────────────────┐
                    │  Local Cache     │
                    │  (~/.cache/)     │
                    └──────────────────┘
```

**Flow:**
1. Client (Pi, Claude, etc.) calls `web_search(query)`
2. MCP attempts to search on current instance
3. If it fails (rate limit, timeout, etc.) → automatically tries next instance
4. If all fail → returns structured error

---

## What Is This?

This MCP server enables AI agents to perform **private** web searches using the SearXNG meta-search engine.

**Features:**
- 🔍 **Private Web Search**: Aggregates results from multiple search engines without tracking
- 🔄 **Automatic Fallback**: Seamlessly switches between instances when one fails
- 🛡️ **Circuit Breaker**: Protects against instances with temporary issues
- 🌐 **Dynamic Discovery**: Automatically discovers healthy instances via searx.space
- 💾 **Local Cache**: Fast startup with cached instance list

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Install dependencies (recommended: use uv)
uv sync
```

### Usage with Pi

```bash
# Add to Pi
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

### Usage as Tool

```javascript
// In Pi or other MCP client
mcp__searxng_web_search__web_search({query: "python programming", results_limit: 5})
```

---

## Tool API

### web_search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search term |
| `results_limit` | number | 10 | Maximum number of results (1-50) |

### Response Example

```json
{
  "success": true,
  "query": "python programming",
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "Experienced programmers in any other language...",
      "engine": "bing"
    }
  ],
  "count": 5,
  "instance_used": "sx.xo.st"
}
```

### Error Response

```json
{
  "success": false,
  "error": "All instances unavailable",
  "message": "Failed to search using any available instance.",
  "details": [
    {"instance": "sx.xo.st", "error": "Request timeout"},
    {"instance": "xka.cz", "error": "Rate limited (429)"}
  ]
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |
| `SEARXNG_TIMEOUT` | `10` | Request timeout in seconds |
| `SEARXNG_INSTANCES` | (auto-discovered) | Comma-separated list of instances |

### Examples

```bash
# Short cache for development
SEARXNG_CACHE_TTL=60 uv run python -m searxng_mcp

# Longer timeout for slow connections
SEARXNG_TIMEOUT=30 uv run python -m searxng_mcp

# Specific instances (optional)
SEARXNG_INSTANCES="https://sx.xo.st,https://search.ctq.ro" uv run python -m searxng_mcp
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Pi/AI)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                      │ MCP Protocol
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SEARXNG MCP SERVER                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  server.py → manager.py → discovery.py                          │  │
│  │                                                               │  │
│  │  • Circuit Breaker (3 failures → 5min cooldown)               │  │
│  │  • Instance Pool (automatic rotation)                          │  │
│  │  • Local Cache (~/.cache/searxng-mcp/)                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐          ┌───────────────────┐         ┌─────────────────┐
│  searx.space  │          │  ~/.cache/        │         │  Public         │
│  (Discovery)  │          │  searxng-mcp/     │         │  Instances       │
│               │          │  instances.json   │         │                 │
└───────────────┘          └───────────────────┘         │  • sx.xo.st     │
                                                          │  • search.ctq.ro│
                                                          │  • xka.cz       │
                                                          └─────────────────┘
```

### Components

| Component | File | Responsibility |
|-----------|------|----------------|
| Server | `server.py` | MCP Interface (FastMCP) |
| Manager | `manager.py` | Instance Pool + Circuit Breaker |
| Discovery | `discovery.py` | Fetch and filter instances from searx.space |
| Models | `models.py` | Data types |
| Constants | `constants.py` | Configuration |

---

## Documentation

### For Users
- [SearXNG Guide](searxng-guide-en.md) - How to use SearXNG for web search
- [Troubleshooting](troubleshooting-en.md) - Common problems and solutions

### For Developers
- [Architecture](architecture.md) - Technical architecture overview
- [Debug Report](docs/developer/mcp-debug-report.md) - MCP debugging history

### Skills
- [SearXNG Skill](docs/skill/searxng-skill.md) - Skill to use with Pi

---

## Troubleshooting

### Common Problems

1. **"All instances unavailable"**
   - No internet or all instances rate limited
   - Solution: `rm -rf ~/.cache/searxng-mcp/`

2. **Rate Limiting (429)**
   - Wait a few minutes
   - System automatically falls back

3. **Timeout**
   - Increase `SEARXNG_TIMEOUT` if needed

See [troubleshooting-en.md](./troubleshooting-en.md) for detailed troubleshooting.

### Debugging

```bash
# View cache
cat ~/.cache/searxng-mcp/instances.json | jq .

# Clear cache
rm -rf ~/.cache/searxng-mcp/

# Test directly
uv run python -c "from searxng_mcp.manager import SearXNGManager; import asyncio; print(asyncio.run(SearXNGManager().search('test', 3)))"
```

---

## Development

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

### Useful Commands

```bash
# Type checking
uv run pyright src/

# Linting
uv run ruff check src/

# Tests
uv run pytest

# With coverage
uv run pytest --cov=src/searxng_mcp --cov-report=term-missing
```

---

## Project Structure

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py          # Exports
│   ├── __main__.py          # Entry point
│   ├── server.py            # FastMCP server
│   ├── manager.py           # Pool + circuit breaker
│   ├── discovery.py         # Instance discovery (searx.space)
│   ├── models.py            # Data models
│   └── constants.py         # Configuration
├── tests/                   # 27 pytest tests
├── docs/
│   ├── usuario/             # User documentation
│   ├── developer/           # Developer documentation
│   └── skill/               # Pi skills
├── memory-bank/             # Project context
├── pyproject.toml
└── README.md
```

---

## License

GPL-3.0
