# SearXNG Instance MCP

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

MCP Server para busca web via SearXNG com fallback automático entre instâncias.

## O que é?

Este servidor MCP permite que agentes de IA façam buscas na web de forma privada, usando o meta-buscador SearXNG. Ele gerencia automaticamente múltiplas instâncias, tentando alternativas quando uma falha.

**Características:**
- 🔍 **Busca Web Privada**: Agrega resultados de múltiplos buscadores sem rastrear
- 🔄 **Fallback Automático**: Troca transparente entre instâncias quando uma falha
- 🛡️ **Circuit Breaker**: Protege contra instâncias com problemas
- 🌐 **Discovery Dinâmico**: Descobre instâncias saudáveis automaticamente
- 💾 **Cache Local**: Inicialização rápida com cache de instâncias

## Documentação

### Para Usuários
- [Guia SearXNG](docs/usuario/searxng-guide.md) - Como usar SearXNG para busca web
- [Troubleshooting](docs/usuario/troubleshooting.md) - Solução de problemas comuns

### Para Desenvolvedores
- [Arquitetura](docs/developer/arquitetura.md) - Visão técnica da arquitetura
- [Debug Report](docs/developer/mcp-debug-report.md) - Histórico de debugging do MCP

### Skills
- [SearXNG Skill](docs/skill/searxng-skill.md) - Skill para usar no Pi

## Quick Start

### Instalação

#### Com uv (recomendado)

```bash
# Clone o repositório
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Instale dependências
uv sync
```

#### Sem uv

```bash
# Clone o repositório
git clone https://github.com/hemeligur/searxng-instance-mcp.git
cd searxng-instance-mcp

# Crie virtualenv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instale dependências
pip install -e .
```

### Uso com Pi

```bash
# Adicione ao Pi
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

### Uso Direto

```bash
# Inicie o servidor (modo stdio)
uv run python -m searxng_mcp
```

### Uso como Tool

```javascript
// No Pi ou outro cliente MCP
mcp__searxng_web_search__web_search({query: "python programming", results_limit: 5})
```

## Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_CACHE_TTL` | `3600` | TTL do cache em segundos (1 hora) |
| `SEARXNG_TIMEOUT` | `10` | Timeout da requisição em segundos |
| `SEARXNG_INSTANCES` | (auto-discovered) | Lista de instâncias separada por vírgulas |

### Exemplo

```bash
# Cache curto para desenvolvimento
SEARXNG_CACHE_TTL=60 uv run python -m searxng_mcp

# Timeout maior para conexões lentas
SEARXNG_TIMEOUT=30 uv run python -m searxng_mcp

# Instâncias específicas
SEARXNG_INSTANCES="https://sx.xo.st,https://searxng.org" uv run python -m searxng_mcp
```

## API da Tool

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
        "description": "Número máximo de resultados (1-50)",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

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

## Arquitetura

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Cliente   │────▶│  SearXNG MCP     │────▶│  Discovery      │
│   (agente)  │◀────│  Server          │◀────│  (searx.space) │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                        │
                           ▼                        ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │  SearXNGManager   │     │  Cache Local    │
                    │  (pool + retry)  │     │  (~/.cache/)    │
                    └──────────────────┘     └─────────────────┘
```

### Componentes

| Componente | Arquivo | Responsabilidade |
|------------|---------|-----------------|
| Server | `server.py` | Interface MCP (FastMCP) |
| Manager | `manager.py` | Pool de instâncias + Circuit Breaker |
| Discovery | `discovery.py` | Busca e filtra instâncias do searx.space |
| Models | `models.py` | Tipos de dados |
| Constants | `constants.py` | Configurações |

### Circuit Breaker

```
CLOSED ──(3 falhas)──▶ OPEN ──(5 min)──▶ HALF_OPEN ──(sucesso)──▶ CLOSED
                                                      │
                                                      └──(falha)──▶ OPEN
```

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

### Estrutura do Projeto

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py          # Exports
│   ├── __main__.py          # Entry point
│   ├── server.py            # FastMCP server
│   ├── manager.py           # Pool + circuit breaker
│   ├── discovery.py         # Instance discovery
│   ├── models.py            # Data models
│   └── constants.py         # Configuration
├── tests/                   # 27 testes pytest
├── docs/
│   ├── usuario/             # Documentação para usuários
│   │   ├── searxng-guide.md
│   │   └── troubleshooting.md
│   ├── developer/           # Documentação para desenvolvedores
│   │   ├── arquitetura.md
│   │   └── mcp-debug-report.md
│   └── skill/               # Skills do Pi
│       └── searxng-skill.md
├── memory-bank/             # Contexto do projeto
├── pyproject.toml
└── README.md
```

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

Consulte [docs/usuario/troubleshooting.md](docs/usuario/troubleshooting.md) para problemas detalhados.

### Debugging

```bash
# Ver cache
cat ~/.cache/searxng-mcp/instances.json | jq .

# Limpar cache
rm -rf ~/.cache/searxng-mcp/

# Testar diretamente
uv run python -c "from searxng_mcp.manager import SearXNGManager; import asyncio; print(asyncio.run(SearXNGManager().search('test', 3)))"
```

## License

GPL-3.0
