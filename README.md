# SearXNG Instance MCP

MCP Server for web search via SearXNG meta-search engine with automatic instance fallback.

## Features

- 🔍 **Web Search**: Search the web using SearXNG meta-search engine
- 🔄 **Automatic Fallback**: Seamlessly switches between instances when one fails
- 🛡️ **Circuit Breaker**: Intelligent retry logic with circuit breaker pattern
- 🌐 **Dynamic Discovery**: Auto-discovers healthy instances from searx.space
- 💾 **Local Cache**: Caches instance list for faster startup

## Installation

```bash
# Clone the repository
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Install dependencies
uv sync
```

## Usage

### As MCP Server

Register with Pi:
```bash
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

Or use the project configuration:
```bash
# Copy .pi/mcp.json to your project
# The server will be auto-discovered by Pi
```

### Command Line

```bash
# Start the server (stdio mode)
uv run python -m searxng_mcp
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |
| `SEARXNG_TIMEOUT` | `10` | Request timeout in seconds |
| `SEARXNG_INSTANCES` | (auto-discovered) | Comma-separated list of instances |

### Custom Instances

```bash
# Override default instances
SEARXNG_INSTANCES="https://sx.xo.st,https://searxng.org" uv run python -m searxng_mcp
```

## MCP Tool

### web_search

```json
{
  "name": "web_search",
  "description": "Busca na web usando meta-buscador SearXNG",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Termo de busca"
      },
      "results_limit": {
        "type": "number",
        "description": "Número máximo de resultados",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

### Example Response

```json
{
  "success": true,
  "query": "python programming",
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "...",
      "engine": "bing"
    }
  ],
  "count": 5,
  "instance_used": "sx.xo.st"
}
```

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  SearXNG MCP     │────▶│  Instance       │
│   (agent)   │◀────│  Server          │◀────│  Discovery      │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                        │
                           ▼                        ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │  SearXNGManager  │     │  searx.space    │
                    │  (pool + retry)  │     │  (API JSON)     │
                    └──────────────────┘     └─────────────────┘
```

## Troubleshooting

### All instances failing

1. Check your internet connection
2. Verify instances are online at https://searx.space
3. Try setting custom instances via `SEARXNG_INSTANCES`

### Rate limiting

Wait a few minutes and retry. The circuit breaker will automatically recover.

### Cache issues

Clear the cache:
```bash
rm -rf ~/.cache/searxng-mcp/
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Type checking
uv run --tool pyright src/

# Run tests
uv run pytest
```

## License

MIT
