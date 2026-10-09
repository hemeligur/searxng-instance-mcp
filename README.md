# SearXNG Instance MCP

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![🇺🇸 English](./docs/EN/README-en.md)](./docs/EN/README-en.md)

**Cliente MCP para busca web via SearXNG** — usa instâncias públicas online com fallback automático.

> ⚠️ **Nota**: Este projeto é um **cliente** que se conecta a instâncias SearXNG públicas/online (como `sx.xo.st`, `search.ctq.ro`). Se você quer rodar sua própria instância SearXNG localmente, consulte [docs/searxng-local.md](docs/searxng-local.md) ou [docs/EN/searxng-local-en.md](docs/EN/searxng-local-en.md) (EN).

---

## Como Funciona

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────────────────┐
│   Cliente   │────▶│  SearXNG MCP     │────▶│  Instâncias Públicas Online │
│   (Pi/AI)   │◀────│  (este projeto)  │◀────│                             │
└─────────────┘      └──────────────────┘      │  • sx.xo.st                 │
                           │                   │  • search.ctq.ro            │
                           │                   │  • searx.space (discovery)  │
                           ▼                   └─────────────────────────────┘
                    ┌──────────────────┐
                    │  Cache Local     │
                    │  (~/.cache/)     │
                    └──────────────────┘
```

**Fluxo:**
1. O cliente (Pi, Claude, etc.) chama `web_search(query)`
2. O MCP tenta buscar na instância atual
3. Se falhar (rate limit, timeout, etc.) → tenta próxima instância automaticamente
4. Se todas falharem → retorna erro estruturado

---

## O que é?

Este servidor MCP permite que agentes de IA façam buscas na web de forma **privada**, usando o meta-buscador SearXNG como cliente.

**Características:**
- 🔍 **Busca Web Privada**: Agrega resultados de múltiplos buscadores sem rastrear
- 🔄 **Fallback Automático**: Troca transparente entre instâncias quando uma falha
- 🛡️ **Circuit Breaker**: Protege contra instâncias com problemas temporários
- 🌐 **Discovery Dinâmico**: Descobre instâncias saudáveis automaticamente via searx.space
- 💾 **Cache Local**: Inicialização rápida com cache de instâncias

---

## Quick Start

### Instalação

```bash
# Clone o repositório
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Instale dependências (recomendado: use uv)
uv sync
```

### Uso com Pi

```bash
# Adicione ao Pi
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

### Uso como Tool

```javascript
// No Pi ou outro cliente MCP
mcp__searxng_web_search__web_search({query: "python programming", results_limit: 5})
```

---

## API da Tool

### web_search

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | string | obrigatório | Termo de busca |
| `results_limit` | number | 10 | Número máximo de resultados (1-50) |

> **Nota sobre `results_limit`**: A API do SearXNG não suporta um parâmetro de limite. O MCP filtra os resultados no lado do cliente, retornando apenas os primeiros N resultados após receber ~10 da API. Para evitar desperdício de requisições, considere usar o cache de resultados (veja [EPD-001](./docs/epd/EPD-001-search-results-cache.md)).

### Exemplo de Resposta

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

### Resposta de Erro

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

## Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_CACHE_TTL` | `3600` | TTL do cache em segundos (1 hora) |
| `SEARXNG_TIMEOUT` | `10` | Timeout da requisição em segundos |
| `SEARXNG_INSTANCES` | (auto-discovered) | Lista de instâncias separada por vírgulas |
| `SEARXNG_DISABLED_INSTANCES` | (vazio) | URLs de instâncias a desabilitar permanentemente |
| `SEARXNG_DEBUG_TOOLS` | `false` | Habilita tools de debug (status, reset, available) |
| `SEARXNG_BACKOFF_BASE` | `60` | Backoff base em segundos |
| `SEARXNG_BACKOFF_MAX` | `900` | Backoff máximo em segundos |

### Exemplos

```bash
# Cache curto para desenvolvimento
SEARXNG_CACHE_TTL=60 uv run python -m searxng_mcp

# Timeout maior para conexões lentas
SEARXNG_TIMEOUT=30 uv run python -m searxng_mcp

# Instâncias específicas (opcional)
SEARXNG_INSTANCES="https://sx.xo.st,https://search.ctq.ro" uv run python -m searxng_mcp

# Desabilitar instâncias com problemas (anti-bot, etc)
SEARXNG_DISABLED_INSTANCES="https://search.ctq.ro" uv run python -m searxng_mcp

# Habilitar tools de debug
SEARXNG_DEBUG_TOOLS=true uv run python -m searxng_mcp
```

### Exemplo: Configuração Completa via Pi

```json
{
  "mcpServers": {
    "searxng-web-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/caminho/para/searxng-instance-mcp",
        "run",
        "python",
        "-m",
        "searxng_mcp"
      ],
      "env": {
        "SEARXNG_DISABLED_INSTANCES": "https://search.ctq.ro,https://bad-instance.com",
        "SEARXNG_DEBUG_TOOLS": "false",
        "SEARXNG_CACHE_TTL": "3600"
      }
    }
  }
}
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE (Pi/AI)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                      │ MCP Protocol
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SEARXNG MCP SERVER                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  server.py → manager.py → discovery.py                          │  │
│  │                                                               │  │
│  │  • Circuit Breaker (3 falhas → 5min cooldown)                 │  │
│  │  • Instance Pool (rotação automática)                          │  │
│  │  • Cache Local (~/.cache/searxng-mcp/)                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐          ┌───────────────────┐         ┌─────────────────┐
│  searx.space  │          │  ~/.cache/        │         │  Instâncias     │
│  (Discovery)  │          │  searxng-mcp/     │         │  Públicas       │
│               │          │  instances.json   │         │                 │
└───────────────┘          └───────────────────┘         │  • sx.xo.st     │
                                                          │  • search.ctq.ro│
                                                          │  • xka.cz       │
                                                          └─────────────────┘
```

### Componentes

| Componente | Arquivo | Responsabilidade |
|------------|---------|-----------------|
| Server | `server.py` | Interface MCP (FastMCP) |
| Manager | `manager.py` | Pool de instâncias + Circuit Breaker |
| Discovery | `discovery.py` | Busca e filtra instâncias do searx.space |
| Persistence | `persistence.py` | Salva/carrega estado em disco |
| Models | `models.py` | Tipos de dados |
| Constants | `constants.py` | Configurações (inclui env vars) |

---

## Documentação

### Para Usuários
- [Guia SearXNG](docs/usuario/searxng-guide.md) - Como usar SearXNG para busca web
- [SearXNG Guide (EN)](docs/EN/searxng-guide-en.md) - How to use SearXNG for web search
- [Troubleshooting](docs/usuario/troubleshooting.md) - Solução de problemas comuns
- [Troubleshooting (EN)](docs/EN/troubleshooting-en.md) - Common problems and solutions

### Para Desenvolvedores
- [Arquitetura](docs/developer/arquitetura.md) - Visão técnica da arquitetura
- [Architecture (EN)](docs/EN/architecture.md) - Technical architecture overview - Visão técnica da arquitetura
- [Debug Report](docs/developer/mcp-debug-report.md) - Histórico de debugging do MCP

### Skills
- [SearXNG Skill](docs/skill/searxng-skill.md) - Skill para usar no Pi

---

## Troubleshooting

### Problemas Comuns

1. **"All instances unavailable"**
   - Sem internet ou todas as instâncias com rate limit
   - Solução: `rm -rf ~/.cache/searxng-mcp/`

2. **Rate Limiting (429)**
   - Aguarde alguns minutos
   - Sistema faz fallback automaticamente

3. **Timeout**
   - Aumente `SEARXNG_TIMEOUT` se necessário

Consulte [docs/usuario/troubleshooting.md](docs/usuario/troubleshooting.md) ou [docs/EN/troubleshooting-en.md](docs/EN/troubleshooting-en.md) para problemas detalhados.

### Debugging

```bash
# Ver cache
cat ~/.cache/searxng-mcp/instances.json | jq .

# Limpar cache
rm -rf ~/.cache/searxng-mcp/

# Testar diretamente
uv run python -c "from searxng_mcp.manager import SearXNGManager; import asyncio; print(asyncio.run(SearXNGManager().search('test', 3)))"
```

---

## Desenvolvimento

### Pré-requisitos
- Python 3.10+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
# Instalar dependências
uv sync

# Instalar dev dependencies
uv sync --extra dev
```

### Comandos Úteis

```bash
# Type checking
uv run pyright src/

# Linting
uv run ruff check src/

# Testes
uv run pytest

# Com coverage
uv run pytest --cov=src/searxng_mcp --cov-report=term-missing
```

---

## Estrutura do Projeto

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
├── tests/                   # 57 testes pytest
├── docs/
│   ├── usuario/             # Documentação para usuários
│   ├── developer/           # Documentação para desenvolvedores
│   └── skill/               # Skills do Pi
├── memory-bank/             # Contexto do projeto
├── pyproject.toml
└── README.md
```

---

## License

GPL-3.0
