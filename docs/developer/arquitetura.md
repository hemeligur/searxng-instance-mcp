# Arquitetura do SearXNG Instance MCP

## Visão Geral

Este documento descreve a arquitetura técnica do servidor MCP para busca web via SearXNG.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENTE (Pi Agent)                            │
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

## Componentes

### 1. Server (`server.py`)

Ponto de entrada do servidor MCP usando FastMCP.

**Responsabilidades:**
- Registrar a ferramenta `web_search`
- Validar e processar requisições
- Serializar respostas para JSON

**Interface exposta:**
```python
@mcp.tool()
async def web_search(query: str, results_limit: int = 10) -> str:
    """Busca na web usando meta-buscador SearXNG com fallback automático."""
```

### 2. Manager (`manager.py`)

Orquestra o pool de instâncias e execução de buscas.

**Responsabilidades:**
- Gerenciar ciclo de vida das instâncias
- Implementar circuit breaker pattern
- Executar busca com fallback
- Rastrear estatísticas de sucesso/falha

**Padrão Circuit Breaker:**
```
CLOSED ──(3 falhas)──▶ OPEN ──(5 min)──▶ HALF_OPEN ──(sucesso)──▶ CLOSED
                                                      │
                                                      └──(falha)──▶ OPEN
```

### 3. Discovery (`discovery.py`)

Descoberta e filtragem de instâncias disponíveis.

**Responsabilidades:**
- Buscar instâncias da API searx.space
- Filtrar por uptime, TLS rank, engines disponíveis
- Cachear resultados localmente
- Fornecer fallback quando API indisponível

**Critérios de filtragem:**
| Critério | Valor Mínimo |
|----------|--------------|
| Uptime | 95% |
| TLS Rank | A+ ou A |
| Engines | google, bing, duckduckgo |

### 4. Models (`models.py`)

Modelos de dados do domínio.

**Classes principais:**
| Classe | Propósito |
|--------|-----------|
| `CircuitState` | Enum para estados do circuit breaker |
| `InstanceStatus` | Status de uma instância individual |
| `SearchResult` | Resultado individual de busca |
| `SearchResponse` | Resposta completa da busca |
| `DiscoveredInstance` | Instância do searx.space |

### 5. Constants (`constants.py`)

Configurações centralizadas do projeto.

## Fluxo de Execução

### 1. Inicialização

```
1. SearXNGManager.__init__()
       │
       ▼
2. _initialize_instances()
       │
       ├──▶ Tentativa 1: discover_instances(use_cache=True)
       │         │
       │         ├── Cache válido ──▶ Retorna instâncias do cache
       │         │
       │         └── Cache inválido ──▶ _fetch_instances_from_api()
       │                                    │
       │                                    └──▶ Se falhar ──▶ FALLBACK_INSTANCES
       │
       └──▶ asyncio.run() falhar ──▶ _load_fallback_instances()
```

### 2. Busca (web_search)

```
1. web_search(query, limit)
       │
       ▼
2. manager.search(query, limit)
       │
       ├──▶ Validar query (não vazia)
       │
       ▼
3. Para cada instância no pool:
       │
       ├──▶ is_available() → Verificar circuit breaker
       │
       ├──▶ Se OPEN com TTL expirado → HALF_OPEN
       │
       ├──▶ _try_instance(url, query, limit)
       │         │
       │         ├── GET /search?q=...&format=json&limit=...
       │         │
       │         └── Parsear resposta JSON
       │
       ├──▶ Se sucesso → Retornar SearchResponse
       │
       └──▶ Se falha → Próxima instância
              │
              └──▶ _update_instance_status(success=False)
                        │
                        └──▶ Se 3 falhas → OPEN
```

### 3. Cache

```
┌─────────────────────────────────────────────────────────────┐
│                      ~/.cache/searxng-mcp/                 │
│                      instances.json                          │
├─────────────────────────────────────────────────────────────┤
│  {                                                          │
│    "timestamp": 1696540800,  // Unix time do cache         │
│    "instances": [                                        │
│      "https://sx.xo.st",                                   │
│      "https://search.ctq.ro",                              │
│      ...                                                   │
│    ]                                                       │
│  }                                                         │
└─────────────────────────────────────────────────────────────┘

TTL padrão: 3600 segundos (1 hora)
```

## Estados do Circuit Breaker

| Estado | Comportamento | Transição |
|--------|--------------|-----------|
| **CLOSED** | Requisições normais | → OPEN após 3 falhas |
| **OPEN** | Requisições bloqueadas | → HALF_OPEN após 5 min |
| **HALF_OPEN** | Uma requisição de teste | → CLOSED (sucesso) ou OPEN (falha) |

## Formato de Resposta

### Sucesso
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

### Erro
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

## Dependências Externas

| Dependência | Versão | Propósito |
|-------------|--------|-----------|
| `fastmcp` | >=4.0.0 | Framework MCP Server |
| `httpx` | >=0.25.0 | Cliente HTTP assíncrono |
| `tenacity` | >=8.0.0 | Retry logic (configurado) |

## API SearXNG

### Endpoint
```
GET https://<instance>/search
```

### Parâmetros
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `q` | string | obrigatório | Query de busca |
| `format` | string | json | Formato da resposta |
| `limit` | int | 10 | Número de resultados (1-50) |

### Resposta SearXNG
```json
{
  "results": [...],
  "answers": [],
  "infoboxes": [],
  "suggestions": [],
  "responses": []
}
```

## Localização de Arquivos

| Item | Caminho |
|------|---------|
| Cache | `~/.cache/searxng-mcp/instances.json` |
| Logs | stderr (via logging Python) |
| Config | Variáveis de ambiente |

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_CACHE_TTL` | 3600 | TTL do cache em segundos |
| `SEARXNG_TIMEOUT` | 10 | Timeout por requisição (s) |
| `SEARXNG_INSTANCES` | (API) | Lista de instâncias (não usado atualmente) |
