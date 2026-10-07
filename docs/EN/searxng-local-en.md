# SearXNG Local (Docker)

[![🇧🇷 Português](../searxng-local.md)](../searxng-local.md)

This document explains how to run a local SearXNG instance, in case you need **maximum privacy** or prefer not to depend on public instances.

> ⚠️ **This MCP does not manage local instances.** It is a client that connects to public/online instances. To run locally, use the options below.

---

## Option 1: Docker Compose (Recommended)

### Installation

```bash
# Clone the official repository
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker

# Edit the .env file with your settings
cp .env.template .env

# Start the container
docker-compose up -d
```

### Configuration

Edit `searxng/data/ultralist.yml` to configure search engines.

### Access

- Web interface: http://localhost:8888
- JSON API: http://localhost:8888/search?q=test&format=json

---

## Option 2: Manual Installation

### Prerequisites

- Python 3.10+
- Node.js (optional, for development)
- nginx (for production)

### Installation

```bash
# Clone the repository
git clone https://github.com/searxng/searxng.git
cd searxng

# Install dependencies
make install

# Install/uwsgi
make install-pyenv

# Configuration
cp searxng/settings.yml searxng/settings.yml
nano searxng/settings.yml

# Run
make run
```

---

## Option 3: SearXNG-ng (Alternative Fork)

```bash
# Clone
git clone https://github.com/searxng/searxng.git searxng-data

# Use the setup script
bash -c "$(curl - https://raw.githubusercontent.com/searxng/searxng-docker/master/run.sh)"
```

---

## Important Settings

### settings.yml

```yaml
search:
  formats:
    - html
    - json

server:
  secret_key: "change-me-to-something-random"
  bind:
    - "0.0.0.0:8888"

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
```

### Disable Logging

```yaml
general:
  instance_name: "my-searxng"
  privacypolicy_url: false
  donation_url: false
  contact_url: false
  enable_metrics: false
```

---

## Comparison: MCP Client vs Local Instance

| Aspect | This MCP (Client) | Local Instance |
|--------|-------------------|-----------------|
| **Privacy** | Good (uses third-party instances) | Maximum (data never leaves) |
| **Maintenance** | Zero (managed automatically) | High (you maintain) |
| **Reliability** | Depends on public instances | 100% under your control |
| **Resources** | Low (HTTP client only) | High (nginx, uwsgi, etc.) |
| **Rate Limiting** | Shared with others | Unlimited (you only) |

---

## When to Use Each Option

### Use This MCP (Client)
- ✅ Fast development
- ✅ Privacy is important but not critical
- ✅ Don't want to maintain infrastructure
- ✅ Want automatic fallback between instances

### Use Local Instance
- ✅ Maximum privacy is essential
- ✅ Want full control over data
- ✅ Have Docker/infrastructure knowledge
- ✅ Want to avoid rate limiting

---

## References

- Official repository: https://github.com/searxng/searxng
- Docker: https://github.com/searxng/searxng-docker
- Documentation: https://docs.searxng.org
