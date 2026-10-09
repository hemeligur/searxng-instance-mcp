# Tech Context

## Stack Técnica

### Runtime
- **Python**: 3.10+
- **Gerenciador**: uv

### Dependências Principais

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| `mcp[cli]` | >=1.0.0 | SDK do Model Context Protocol |
| `httpx` | >=0.25.0 | Cliente HTTP assíncrono |
| `tenacity` | >=8.0.0 | Retry logic |

### Estrutura do Projeto

```
searxng-instance-mcp/
├── src/
│   └── searxng_mcp/
│       ├── __init__.py        # Exports principais
│       ├── __main__.py        # Entry point (uv run python -m searxng_mcp)
│       ├── server.py          # Servidor FastMCP principal
│       ├── manager.py          # SearXNGManager (pool + retry)
│       ├── discovery.py       # InstanceDiscovery (searx.space)
│       ├── constants.py       # Constantes e configurações
│       └── models.py          # Modelos de dados
├── .pi/
│   ├── mcp.json              # Configuração MCP do Pi
│   └── rules/
│       └── memory-bank.md    # Rule de memória
├── memory-bank/
│   ├── 01-projectBrief.md
│   ├── 02-productContext.md
│   ├── 03-systemPatterns.md
│   ├── 04-techContext.md
│   ├── 05-progress.md
│   ├── 06-activeContext.md
│   └── 07-tasks.md
├── pyproject.toml
└── README.md
```

## API SearXNG

### Endpoint
```
GET https://<instancia>/search
```

### Parâmetros
| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `q` | Query de busca | `q=python+tutorial` |
| `format` | Formato da resposta | `format=json` |
| `lang` | Idioma | `lang=pt-BR` |
| `pageno` | Número da página | `pageno=1` |
| `safesearch` | Filtro safe search (0-2) | `safesearch=0` |

**Nota**: O parâmetro `limit` **não é suportado** pela API do SearXNG. O número de resultados é fixo (~10 por página). Referência: https://docs.searxng.org/dev/search_api.html

**Solução Implementada**: O MCP filtra os resultados no lado do cliente após recebê-los da API. Para evitar desperdício, considere implementar o cache de resultados conforme [EPD-001](./docs/epd/EPD-001-search-results-cache.md).
| `lang` | Idioma | `lang=pt-BR` |

### Exemplo de Requisição
```bash
curl "https://sx.xo.st/search?q=python&format=json&limit=5"
```

## Configuração do Pi

### .pi/mcp.json
```json
{
  "mcpServers": {
    "searxng-web-search": {
      "command": "uv",
      "args": ["run", "python", "-m", "searxng_mcp"],
      "description": "Web search via SearXNG with automatic instance fallback"
    }
  }
}
```

### Variáveis de Ambiente
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_INSTANCES` | (API searx.space) | Lista de instâncias separada por vírgulas |
| `SEARXNG_CACHE_TTL` | 3600 | TTL do cache em segundos |
| `SEARXNG_TIMEOUT` | 10 | Timeout por requisição (s) |
| `SEARXNG_DISABLED_INSTANCES` | (vazio) | URLs de instâncias a desabilitar (separadas por vírgula) |
| `SEARXNG_DEBUG_TOOLS` | false | Habilita tools de debug (get_instances_status, reset_instance, get_available_instances) |
| `SEARXNG_BACKOFF_BASE` | 60 | Backoff base em segundos |
| `SEARXNG_BACKOFF_MAX` | 900 | Backoff máximo em segundos (15 min) |

## Ferramenta MCP Exposta

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

## Cache Local

- **Local**: `~/.cache/searxng-mcp/`
- **Arquivo**: `instances.json`
- **Formato**: JSON com timestamp e lista de instâncias
- **TTL**: 1 hora (configurável)
