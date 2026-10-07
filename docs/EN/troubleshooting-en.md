# Troubleshooting - SearXNG Instance MCP

[![🇧🇷 Português](../usuario/troubleshooting.md)](../usuario/troubleshooting.md)

## Common Problems and Solutions

### 1. "All instances unavailable"

**Symptom:**
```json
{
  "success": false,
  "error": "All instances unavailable"
}
```

**Possible causes:**
- No internet connection
- All instances are rate limited
- Firewall blocking requests
- searx.space API unavailable

**Solutions:**

1. **Check internet connection:**
```bash
curl -s https://sx.xo.st/search?q=test&format=json
```

2. **Wait and try again:**
   - Rate limits are temporary (usually 5-15 minutes)

3. **Clear cache to force new discovery:**
```bash
rm -rf ~/.cache/searxng-mcp/
```

4. **Use specific instances via environment variables:**
```bash
SEARXNG_CACHE_TTL=0 uv run python -m searxng_mcp
```

---

### 2. Rate Limiting

**Symptom:**
```json
{
  "error": "Rate limited (429)"
}
```

**Solutions:**

1. **Wait** - Rate limits expire automatically in a few minutes

2. **The system automatically falls back** to other instances

3. **Clear cache** to use different instances:
```bash
rm -rf ~/.cache/searxng-mcp/
```

---

### 3. Timeout on All Instances

**Symptom:**
```json
{
  "error": "Request timeout"
}
```

**Causes:**
- Instance overloaded
- Network issues
- Firewall

**Solutions:**

1. **Check connectivity:**
```bash
ping -c 3 sx.xo.st
```

2. **Clear cache** to try different instances:
```bash
rm -rf ~/.cache/searxng-mcp/
```

3. **Increase timeout** (requires code modification):
```python
# In constants.py
DEFAULT_TIMEOUT: int = 30  # seconds
```

---

### 4. MCP Server Not Connecting

**Symptom:**
```
searxng-web-search: not connected
```

**Solutions:**

1. **Remove and add again:**
```bash
pi mcp remove searxng-web-search
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

2. **Verify the project is in the correct path:**
```bash
ls /path/to/searxng-instance-mcp/src/searxng_mcp/
```

3. **Verify dependencies:**
```bash
cd /path/to/searxng-instance-mcp
uv sync
uv run python -c "from searxng_mcp import main; print('OK')"
```

---

### 5. Query Returns Empty Results

**Symptom:**
```json
{
  "success": true,
  "query": "xyz",
  "results": [],
  "count": 0
}
```

**Solutions:**

1. **Check the query** - very specific terms may have no results

2. **Try with a more generic term:**
```python
# Example
query = "python"  # Works
query = "xyz123nonexistent999"  # Doesn't work
```

3. **Clear cache** to ensure updated instances:
```bash
rm -rf ~/.cache/searxng-mcp/
```

---

### 6. Stale Cache

**Symptom:**
- Using instances that no longer exist
- Instances with different status

**Solutions:**

1. **Clear manually:**
```bash
rm -rf ~/.cache/searxng-mcp/
```

2. **Wait for expiration** (1 hour by default)

3. **Reset TTL via environment variable:**
```bash
SEARXNG_CACHE_TTL=0 uv run python -m searxng_mcp
```

---

### 7. Import Error

**Symptom:**
```
ModuleNotFoundError: No module named 'searxng_mcp'
```

**Solutions:**

1. **Install dependencies:**
```bash
uv sync
```

2. **Verify you're in the correct directory:**
```bash
cd /path/to/searxng-instance-mcp
```

3. **Run the project:**
```bash
uv run python -m searxng_mcp
```

---

## Debug Commands

### View Cache Status
```bash
cat ~/.cache/searxng-mcp/instances.json | jq .
```

### Verify Instances
```python
from searxng_mcp.discovery import discover_instances
import asyncio

instances = asyncio.run(discover_instances(use_cache=False))
print(instances)
```

### Test Manager
```python
from searxng_mcp.manager import SearXNGManager
import asyncio

manager = SearXNGManager()
result = asyncio.run(manager.search("python", limit=5))
print(result.to_dict())
```

### View Logs
```bash
# Run with debug output
uv run python -m searxng_mcp 2>&1 | grep -i "searxng"
```

---

## Advanced Debugging

### 1. Enable Detailed Logging

Create file `debug_test.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from searxng_mcp.manager import SearXNGManager
import asyncio

async def main():
    manager = SearXNGManager()
    result = await manager.search("python", limit=3)
    print(result.to_dict())

asyncio.run(main())
```

Run:
```bash
uv run python debug_test.py
```

### 2. Check Circuit Breaker

```python
from searxng_mcp.manager import SearXNGManager

manager = SearXNGManager()
summary = manager.get_status_summary()
print(summary)
```

### 3. Test Specific Instance

```python
import httpx
import asyncio

async def test_instance():
    url = "https://sx.xo.st/search"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params={"q": "test", "format": "json"})
        print(response.json())

asyncio.run(test_instance())
```

---

## Contact and Support

- **GitHub Issue:** https://github.com/hemeligur/searxng-instance-mcp/issues
- **SearXNG Documentation:** https://docs.searxng.org
- **SearXNG Instances Status:** https://searx.space
