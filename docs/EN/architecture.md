# Architecture - SearXNG Instance MCP

[![🇧🇷 Português](../developer/arquitetura.md)](../developer/arquitetura.md)

This document describes the technical architecture of the MCP server for web search via SearXNG.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Pi Agent)                             │
│                         mcp__searxng_web_search__web_search()          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol (JSON-RPC)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SEARXNG MCP SERVER                             │
│                        (FastMCP, Python 3.10+)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     server.py                                    │   │
│  │  ┌─────────────┐    ┌──────────────────────────────────────┐   │   │
│  │  │ web_search  │───▶│           SearXNGManager             │   │   │
│  │  │  (tool)     │    │                                       │   │   │
│  │  └─────────────┘    │  - Instance Pool                      │   │   │
│  │                     │  - Circuit Breaker                    │   │   │
│  │                     │  - Search Execution                   │   │   │
│  │                     └──────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
           ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
           │  Discovery  │  │   Cache     │  │  Instance   │
           │  (API)      │  │  (Local)    │  │  Pool       │
           └─────────────┘  └─────────────┘  └─────────────┘
                    │               │               │
                    ▼               ▼               ▼
           ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
           │ searx.space │  │ ~/.cache/   │  │  SearXNG    │
           │  (API)      │  │ searxng-mcp │  │  Instances  │
           └─────────────┘  └─────────────┘  └─────────────┘
```

## Components

### 1. Server (`server.py`)

MCP server entry point using FastMCP.

**Responsibilities:**
- Register the `web_search` tool
- Validate and process requests
- Serialize responses to JSON

**Exposed Interface:**
```python
@mcp.tool()
async def web_search(query: str, results_limit: int = 10) -> str:
    """Search the web using SearXNG meta-search engine with automatic fallback."""
```

### 2. Manager (`manager.py`)

Orchestrates the instance pool and search execution.

**Responsibilities:**
- Manage instance lifecycle
- Implement circuit breaker pattern
- Execute search with fallback
- Track success/failure statistics

**Circuit Breaker Pattern:**
```
CLOSED ──(3 failures)──▶ OPEN ──(5 min)──▶ HALF_OPEN ──(success)──▶ CLOSED
                                                      │
                                                      └──(failure)──▶ OPEN
```

### 3. Discovery (`discovery.py`)

Discovers and filters available instances.

**Responsibilities:**
- Fetch instances from searx.space API
- Filter by uptime, TLS rank, available engines
- Cache results locally
- Provide fallback when API is unavailable

**Filtering Criteria:**
| Criterion | Minimum Value |
|-----------|---------------|
| Uptime | 95% |
| TLS Rank | A+ or A |
| Engines | google, bing, duckduckgo |

### 4. Models (`models.py`)

Domain data models.

**Main Classes:**
| Class | Purpose |
|-------|---------|
| `CircuitState` | Enum for circuit breaker states |
| `InstanceStatus` | Status of an individual instance |
| `SearchResult` | Individual search result |
| `SearchResponse` | Complete search response |
| `DiscoveredInstance` | Instance from searx.space |

### 5. Persistence (`persistence.py`)

Handles saving and loading instance state to disk.

**Responsibilities:**
- Save circuit breaker and backoff state to `~/.cache/searxng-mcp/instance_state.json`
- Load state on startup
- Filter out disabled instances (not persisted)

### 6. Constants (`constants.py`)

Centralized project configuration including environment variable helpers.

## Execution Flow

### 1. Initialization

```
1. SearXNGManager.__init__()
       │
       ▼
2. _initialize_instances()
       │
       ├──▶ Attempt 1: discover_instances(use_cache=True)
       │         │
       │         ├── Valid cache ──▶ Return cached instances
       │         │
       │         └── Invalid cache ──▶ _fetch_instances_from_api()
       │                                    │
       │                                    └──▶ If fails ──▶ FALLBACK_INSTANCES
       │
       └──▶ If asyncio.run() fails ──▶ _load_fallback_instances()
```

### 2. Search (web_search)

```
1. web_search(query, limit)
       │
       ▼
2. manager.search(query, limit)
       │
       ├──▶ Validate query (not empty)
       │
       ▼
3. For each instance in pool:
       │
       ├──▶ is_available() → Check circuit breaker
       │
       ├──▶ If OPEN with expired TTL → HALF_OPEN
       │
       ├──▶ _try_instance(url, query, limit)
       │         │
       │         ├── GET /search?q=...&format=json&limit=...
       │         │
       │         └── Parse JSON response
       │
       ├──▶ If success → Return SearchResponse
       │
       └──▶ If failure → Next instance
              │
              └──▶ _update_instance_status(success=False)
                        │
                        └──▶ If 3 failures → OPEN
```

### 3. Cache

```
┌─────────────────────────────────────────────────────────────┐
│                      ~/.cache/searxng-mcp/                 │
│                      instances.json                          │
├─────────────────────────────────────────────────────────────┤
│  {                                                          │
│    "timestamp": 1696540800,  // Unix time of cache         │
│    "instances": [                                        │
│      "https://sx.xo.st",                                   │
│      "https://search.ctq.ro",                              │
│      ...                                                   │
│    ]                                                       │
│  }                                                         │
└─────────────────────────────────────────────────────────────┘

Default TTL: 3600 seconds (1 hour)
```

## Circuit Breaker States

| State | Behavior | Transition |
|-------|----------|------------|
| **CLOSED** | Normal requests | → OPEN after 3 failures |
| **OPEN** | Requests blocked | → HALF_OPEN after 5 min |
| **HALF_OPEN** | One test request | → CLOSED (success) or OPEN (failure) |

## Response Format

### Success
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

### Error
```json
{
  "success": false,
  "query": "test",
  "error": "All instances unavailable",
  "message": "Failed to search using any available instance.",
  "details": [
    {"instance": "sx.xo.st", "error": "Request timeout"},
    {"instance": "xka.cz", "error": "Rate limited (429)"}
  ]
}
```

## External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `fastmcp` | >=4.0.0 | MCP Server Framework |
| `httpx` | >=0.25.0 | Async HTTP Client |
| `tenacity` | >=8.0.0 | Retry logic (configured) |

## SearXNG API

### Endpoint
```
GET https://<instance>/search
```

### Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `format` | string | json | Response format |
| `limit` | int | 10 | Number of results (1-50) |

### SearXNG Response
```json
{
  "results": [...],
  "answers": [],
  "infoboxes": [],
  "suggestions": [],
  "responses": []
}
```

## File Locations

| Item | Path |
|------|------|
| Cache | `~/.cache/searxng-mcp/instances.json` |
| Logs | stderr (via Python logging) |
| Config | Environment variables |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_CACHE_TTL` | 3600 | Cache TTL in seconds |
| `SEARXNG_TIMEOUT` | 10 | Request timeout (s) |
| `SEARXNG_INSTANCES` | (API) | Instance list (comma-separated) |
| `SEARXNG_DISABLED_INSTANCES` | (empty) | Instances to permanently disable |
| `SEARXNG_DEBUG_TOOLS` | false | Enable debug tools (get_instances_status, reset_instance, get_available_instances) |
| `SEARXNG_BACKOFF_BASE` | 60 | Backoff base in seconds |
| `SEARXNG_BACKOFF_MAX` | 900 | Backoff max in seconds (15 min) |
