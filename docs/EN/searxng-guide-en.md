# Guide: Web Search with SearXNG

[![🇧🇷 Português](../usuario/searxng-guide.md)](../usuario/searxng-guide.md)

## What is SearXNG?

SearXNG is a **private, free** meta-search engine that aggregates results from various search engines (Google, Bing, DuckDuckGo, etc.) without tracking or profiling users.

---

## Instance Index

### 🌐 https://searx.space

This is the **official website** that lists all public SearXNG instances.

**Available data:**
- Uptime status for each instance
- Enabled search engines
- Success rate per engine
- Geographic location of servers
- Security rating (Mozilla Observatory)

### How to filter good instances

On searx.space, look for instances with:
- ✅ **High uptime** (>95%)
- ✅ **TLS Grade A+**
- ✅ **Multiple working engines** (google, bing, duckduckgo)
- ✅ **No excessive rate limiting**

---

## Recommended Instances for Testing

| URL | Status | Notes |
|-----|--------|-------|
| `https://sx.xo.st` | ✅ Good | 100% uptime, fast |
| `https://xka.cz` | ⚠️ Rate limit | Works, but with limits |
| `https://search.ctq.ro` | ✅ Good | 100% uptime, TLS A+ |

---

## SearXNG JSON API

### Base Endpoint

```
GET https://<instance>/search
```

### Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `q` | Search query | `q=python+tutorial` |
| `format` | Response format | `format=json` |
| `engines` | Specific engines | `engines=google,bing` |
| `lang` | Language | `lang=en` |
| `limit` | Number of results | `limit=10` |
| `categories` | Category | `categories=general` |

### Complete Example

```bash
curl -s "https://sx.xo.st/search?q=python+programming&format=json&limit=5"
```

### JSON Response

```json
{
  "query": "python programming",
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "Experienced programmers in any other language...",
      "engine": "bing",
      "category": "general"
    }
  ],
  "infoboxes": [],
  "suggestions": [],
  "answers": []
}
```

---

## How to Use in Pi

### Option 1: Bash (Direct)

```bash
curl -s "https://sx.xo.st/search?q=term&format=json"
```

### Option 2: Pi Skill

Create the file `~/.pi/skills/searxng.md`:

```markdown
# SearXNG Web Search

Web search using SearXNG (privacy-first).

## Command

```bash
curl -s "https://sx.xo.st/search?q={{query}}&format=json"
```

## Arguments

- `query`: Search term (use + for spaces)

## Output

JSON results with title, URL and description.

## Example

Input: `query=javascript framework 2024`
```

Then reload Pi with `/reload`.

---

## Common Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `Too Many Requests` | Rate limit | Wait or switch instance |
| `No result` | IP blocked | Try another instance |
| `Access denied` | Firewall | Use VPN or another instance |
| `Timeout` | Engine overloaded | Retry with specific engines |

---

## Best Practices

### 1. Instance Rotation

Don't abuse a single instance. If you get rate limit:

```bash
# Try these in order
INSTANCES=("sx.xo.st" "xka.cz" "search.ctq.ro")

for inst in "${INSTANCES[@]}"; do
  result=$(curl -s "https://$inst/search?q=test&format=json")
  if [ -n "$result" ]; then
    echo "$result"
    break
  fi
done
```

### 2. Use Specific Engines

If an engine is blocked, request others:

```bash
curl "https://sx.xo.st/search?q=test&engines=bing,duckduckgo&format=json"
```

### 3. Avoid Excessive Searches

SearXNG is free and maintained by volunteers. Don't do:
- 🔴 Mass scraping
- 🔴 Aggressive automation
- 🔴 Loop searches

---

## Verified Public Instances

### Working in 2026-10-05

```
https://sx.xo.st        # Fast, good uptime
https://xka.cz          # 100% uptime, but with rate limit
https://www.gruble.de   # Good for DE
https://www.isci.si     # Backup
```

### Trusted Instances
```
https://sx.xo.st        # Fast, good uptime
https://search.ctq.ro   # 100% uptime, TLS A+
```

> ⚠️ **Note**: `https://searxng.org` is the **official website/documentation** of the project, not a public search instance.

---

## FAQ

**Q: Is it safe to use public instances?**
A: Yes. SearXNG doesn't store cookies or logs. But for maximum privacy, run your own instance.

**Q: Why are some results duplicated?**
A: Meta-search aggregates from multiple engines. Use `engines=` to limit.

**Q: How do I find faster instances?**
A: Check the `timing.search` field on searx.space. Lower values = faster.

---

## References

- Repository: https://github.com/searxng/searxng
- Documentation: https://docs.searxng.org
- Instances: https://searx.space
- Search API: https://docs.searxng.org/dev/search_api.html
