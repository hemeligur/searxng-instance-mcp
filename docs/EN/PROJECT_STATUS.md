# Project Status - SearXNG Instance MCP

> **Last Updated**: October 2026

## Current Status

| Aspect | Status | Notes |
|--------|--------|-------|
| **Core Functionality** | ✅ Working | Circuit breaker, fallback, persistence all implemented |
| **Public Instances** | ⚠️ Unreliable | ~99% of public instances have issues |
| **Use in Production** | ❌ Not Recommended | Use local instance or commercial API instead |
| **Code Quality** | ✅ High | 66 tests, type hints, good architecture |

---

## The Problem with Public Instances

### Reality Check (October 2026)

When testing the project, we found that **public SearXNG instances are not reliable**:

| Metric | Value |
|--------|-------|
| Instances checked | ~96 |
| Working normally | <1% |
| Rate limited | ~90% |
| Anti-bot blocking | ~5% |
| Unavailable | ~4% |

### Why This Happens

1. **No SLA**: Public instances are maintained by volunteers with no uptime guarantees
2. **Resource constraints**: Many run on limited bandwidth/cpu
3. **Abuse**: Some users abuse instances, forcing operators to add limits
4. **No official API**: Unlike commercial services, there's no "enterprise tier"

### What This Means for This Project

The **code architecture is solid**:
- Circuit breaker works ✅
- Fallback logic works ✅
- Cache and persistence work ✅
- 66 tests passing ✅

But the **infrastructure it depends on is unreliable** - and that's outside our control.

---

## Who Should Use This Project?

### ✅ Good Fit
- **Experimentation**: Learning about MCP, SearXNG, circuit breaker patterns
- **Local Development**: Testing with a local SearXNG instance
- **Custom Infrastructure**: Running your own SearXNG instance pool

### ❌ Not Recommended
- **Production Systems**: Need guaranteed uptime? Use SerpAPI or similar
- **User-Facing Applications**: Public instances will fail at the worst times
- **Time-Critical Searches**: No guarantees on response time

---

## Alternatives

### For Production Use

| Service | Free Tier | Reliability | Notes |
|---------|-----------|------------|-------|
| [SerpAPI](https://serpapi.com/) | 100 searches/month | High | Paid after free tier |
| [Google Custom Search](https://developers.google.com/custom-search) | 100 searches/day | High | Requires Google account |
| [DuckDuckGo API](https://duckduckgo.com/api) | Limited | Medium | Free but restricted |
| [Bing Web Search](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) | $5/10k queries | High | Azure subscription needed |

### For Self-Hosted SearXNG

If you want the privacy benefits of SearXNG with reliable uptime:

```bash
# Quick Docker setup
docker run --rm -p 8888:8888 \
  -e SEARXNG_BASE_URL=http://localhost:8888/ \
  searxng/searxng

# Then configure MCP
SEARXNG_INSTANCES="http://localhost:8888" \
  SEARXNG_DEBUG_TOOLS=true \
  uv run python -m searxng_mcp
```

---

## Future Possibilities

This project could be useful if:

1. **You run your own instance pool**: The circuit breaker and fallback logic would be valuable
2. **SearXNG launches official API**: A hosted version with SLA would change everything
3. **Community instance network**: Cooperative hosting with uptime guarantees

---

## Contributing

If you're interested in improving this project:

1. **Local instance support**: Better configuration for self-hosted setups
2. **Alternative backends**: Support for SerpAPI or similar as fallback
3. **Health checking**: Proactive monitoring of instance availability

---

## Conclusion

This was a valuable learning project about:
- MCP server development
- Circuit breaker patterns
- Async Python programming
- Building resilient systems

The **code is good**. The **premise** (relying on public instances) wasn't realistic.

If you found this useful for learning, great! If you need production web search, use a commercial service or run your own SearXNG instance.

---

*This document exists to set honest expectations for anyone finding this project.*
