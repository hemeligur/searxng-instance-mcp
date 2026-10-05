# Tasks

## Backlog

### Fase 1: Estrutura Base
- [x] **T-001**: Criar `pyproject.toml` com dependências (mcp[cli], httpx, tenacity)
- [x] **T-002**: Criar estrutura de diretórios `src/searxng_mcp/`
- [x] **T-003**: Criar `src/searxng_mcp/__init__.py` exportando servidor
- [x] **T-004**: Criar `src/searxng_mcp/models.py` com dataclasses

### Fase 2: Discovery Dinâmico
- [x] **T-010**: Implementar `InstanceDiscovery` em `discovery.py` ✅
  - Buscar instâncias de `https://searx.space/api/v1/instances`
  - Filtrar por: `uptime > 95%`, `network/tls_rank == A+`, `engines` principais
  - Implementar cache local em `~/.cache/searxng-mcp/instances.json`
  - TTL configurável (padrão: 1 hora)
- [x] **T-011**: Definir `FALLBACK_INSTANCES` hardcoded ✅
  - `https://sx.xo.st`
  - `https://searxng.org`
  - `https://xka.cz`

### Fase 3: Gerenciamento de Pool
- [x] **T-020**: Implementar `SearXNGManager` em `manager.py` ✅
  - Carregar instâncias via `InstanceDiscovery`
  - Implementar circuit breaker:
    - Estados: CLOSED, OPEN, HALF_OPEN
    - TTL: 5 minutos
  - Método `search(query, limit)` com retry em cascata
  - Tracking de instância usada (para logs/debug)

### Fase 4: Servidor MCP
- [x] **T-030**: Implementar `server.py` com SDK MCP ✅
  - Expor ferramenta `web_search(query, results_limit)`
  - Validar inputs
  - Tratar erros e retornar resposta padronizada
- [x] **T-031**: Implementar `main()` com initialization do servidor ✅

### Fase 5: Configuração Pi
- [x] **T-040**: Criar `.pi/mcp.json` com configuração do servidor ✅
- [x] **T-041**: Documentar comando de registro ✅
  - `pi mcp add searxng-web-search -- uv run python -m searxng_mcp`

### Fase 6: Documentação
- [x] **T-050**: Criar `README.md` com: ✅
  - Instalação (`uv sync`)
  - Uso da ferramenta `web_search`
  - Configuração de instâncias customizadas
  - Variáveis de ambiente
  - Troubleshooting

### Fase 7: Testes
- [x] **T-060**: Teste básico de conexão com instância ✅
- [x] **T-061**: Teste de fallback (forçar falha de uma instância) ✅
- [x] **T-062**: Teste de cache de instâncias ✅

---

## Detalhamento: T-010 - InstanceDiscovery

### Responsabilidade
Buscar e filtrar instâncias SearXNG do indexador oficial.

### API do searx.space
```
GET https://searx.space/api/v1/instances
```

### Resposta Esperada
```json
{
  "instances": [
    {
      "name": "sx.xo.st",
      "url": "https://sx.xo.st",
      "network": {
        "uptime": 100,
        "tls_rank": "A+"
      },
      "engines": ["google", "bing", "duckduckgo"]
    }
  ]
}
```

### Critérios de Filtragem
```python
INSTANCES_FILTER = {
    "min_uptime": 95,           # percentual
    "required_tls_rank": "A+", # ou A
    "required_engines": ["google", "bing", "duckduckgo"],
    "max_instances": 20        # limite do pool
}
```

### Cache
- **Path**: `~/.cache/searxng-mcp/instances.json`
- **Formato**:
```json
{
  "timestamp": 1696500000,
  "instances": ["https://sx.xo.st", "https://searxng.org", ...]
}
```

---

## Detalhamento: T-020 - SearXNGManager

### Responsabilidade
Gerenciar pool de instâncias e orquestrar buscas com fallback.

### Fluxo do `search()`
```
1. Para cada instância (ordenada por freshness):
   a. Verificar circuit breaker
   b. Se OPEN → pular
   c. Se HALF_OPEN ou CLOSED:
      - Fazer GET /search?q={query}&format=json&limit={limit}
      - Se sucesso: marcar CLOSED, retornar resultados
      - Se falha: marcar OPEN, continuar para próxima

2. Se todas falharem:
   - Retornar erro estruturado
```

### Circuit Breaker
```python
class CircuitState(Enum):
    CLOSED = "closed"      # Normal, aceita requisições
    OPEN = "open"          # Bloqueia requisições
    HALF_OPEN = "half_open"  # Testa se voltou

# TTL: 5 minutos para OPEN → HALF_OPEN
# Sucesso em HALF_OPEN → CLOSED
# Falha em HALF_OPEN → OPEN (volta a esperar TTL)
```

### Retry Strategy
```python
RETRY_CONFIG = {
    "max_retries_per_instance": 1,
    "timeout_per_request": 10,  # segundos
    "backoff_factor": 0,  # sem backoff, próxima instância é diferente
}
```

---

## Detalhamento: T-030 - web_search

### Input
| Campo | Tipo | Obrigatório | Padrão | Descrição |
|-------|------|-------------|--------|-----------|
| `query` | string | Sim | - | Termo de busca |
| `results_limit` | number | Não | 10 | Limite de resultados |

### Output Sucesso
```json
{
  "success": true,
  "query": "python programming",
  "results": [
    {
      "url": "https://...",
      "title": "...",
      "content": "...",
      "engine": "google"
    }
  ],
  "count": 5,
  "instance_used": "sx.xo.st"
}
```

### Output Erro
```json
{
  "success": false,
  "error": "all_instances_failed",
  "message": "Todas as instâncias SearXNG falharam após retries",
  "details": [
    {"instance": "sx.xo.st", "error": "rate_limit", "code": 429},
    {"instance": "xka.cz", "error": "timeout", "code": null}
  ]
}
```

---

## Notas de Implementação

1. **Usar httpx.AsyncClient** para requisições assíncronas
2. **Usar tenacity** para retry logic
3. **Logging** com `structlog` ou `loguru` para debugging
4. **Type hints** em todas as funções públicas
5. **Testar comuv run --tool pyright** para type checking

---

## Fix Realizado (2025-10-06)

### Problema
- Servidor MCP original usava API antiga (`mcp[cli]>=1.0.0` com `add_request_handler`)
- Erro `Invalid request parameters` ao chamar via Pi

### Solução
- Migrou para **FastMCP 4** (`fastmcp>=4.0.0`)
- Usa decorator `@mcp.tool()` em vez de handlers manuais
- Schema de input gerado automaticamente via type hints

### Commit
- Branch: `fix/fastmcp-migration`
- Commit: `0822031`

### Código Antes/Depois

**Antes (API antiga):**
```python
from mcp.server import Server
server = Server(APP_NAME)
server.add_request_handler("tools/list", ListToolsRequest, list_tools_handler)
server.add_request_handler("tools/call", CallToolRequest, call_tool_handler)
```

**Depois (FastMCP):**
```python
from fastmcp import FastMCP
mcp = FastMCP("searxng-web-search")

@mcp.tool()
async def web_search(query: str, results_limit: int = 10) -> str:
    ...
```
