# Progress

## Status Geral
🟢 **Testes Implementados** - Aguardando execução

## Marcos

- [x] Memory Bank inicializado
- [x] Plano de tarefas documentado
- [x] Estrutura base do projeto criada (pyproject.toml, diretórios)
- [x] Implementação do discovery dinâmico
- [x] Implementação do SearXNGManager
- [x] Implementação do servidor MCP
- [x] Configuração do Pi (.pi/mcp.json)
- [x] Documentação README.md
- [x] Testes pytest implementados (T-060, T-061, T-062)

## Histórico de Mudanças

### 2025-10-06 (Tarde)
- **T-060, T-061, T-062**: Suite de testes pytest implementada
  - `tests/__init__.py` - package marker
  - `tests/conftest.py` - fixtures (mock_httpx_response, sample_*, temp_cache_dir)
  - `tests/test_discovery.py` - testes de descoberta e filtragem
  - `tests/test_manager.py` - testes de busca, fallback e circuit breaker
  - `tests/test_cache.py` - testes de cache
  - pytest>=7.0, pytest-asyncio>=0.21, pytest-mock>=3.10 adicionados ao pyproject.toml

### 2025-10-06 (Manhã)
- **Orquestração completa** executada via skill orchestrate-tasks
- **Fase 5 (T-040, T-041)**: `.pi/mcp.json` criado
  - Command: `uv run python -m searxng_mcp`
  - Env vars: SEARXNG_CACHE_TTL, SEARXNG_TIMEOUT
- **Fase 6 (T-050)**: README.md completo
  - Installation, usage, configuration
  - Environment variables
  - Architecture diagram
  - Troubleshooting guide
- Commits consolidados: `13c5755`

### 2025-10-06 (Madrugada)
- **T-020**: Implementado `SearXNGManager` em `manager.py`
  - Circuit breaker com estados CLOSED → OPEN → HALF_OPEN
  - TTL de 5 minutos para transição OPEN → HALF_OPEN
  - Método `search()` com fallback automático entre instâncias
  - `_try_instance()` para requisições assíncronas
  - `get_status_summary()` para debugging
  - `reset_circuit()` para reset manual
- **T-030, T-031**: Corrigido servidor MCP
  - API correta do MCP SDK (add_request_handler)
  - Handler `list_tools_handler()` e `call_tool_handler()`
  - Validação de inputs e tratamento de erros robusto

### 2025-10-05
- **T-010**: Implementado `discovery.py`
  - `discover_instances()` - busca e filtra instâncias do searx.space API
  - Cache em `~/.cache/searxng-mcp/instances.json` com TTL configurável
  - Fallback para instâncias hardcoded quando API indisponível
- **T-011**: Definidas constantes em `constants.py`
  - FALLBACK_INSTANCES, DEFAULT_TIMEOUT, CACHE_TTL, etc.
- Repositório GitHub criado (privado): `hemeligur/searxng-instance-mcp`

### 2025-10-05 (Início)
- Memory bank inicializado
- Plano documentado em 07-tasks.md
- **T-001 a T-004**: Estrutura base implementada
  - `pyproject.toml` com dependências (mcp, httpx, tenacity)
  - `src/searxng_mcp/` com `__init__.py`, `models.py`, `server.py`
  - README.md criado
  - Dependências instaladas via `uv sync`

## Repositório

**URL:** https://github.com/hemeligur/searxng-instance-mcp  
**Visibilidade:** 🔒 PRIVATE

## Estrutura do Projeto

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py       # exports main
│   ├── constants.py      # FALLBACK_INSTANCES, configs
│   ├── discovery.py      # InstanceDiscovery (searx.space API)
│   ├── manager.py        # SearXNGManager (pool + circuit breaker)
│   ├── models.py         # CircuitState, SearchResult, etc.
│   └── server.py         # MCP server com web_search
├── tests/
│   ├── __init__.py       # package marker
│   ├── conftest.py       # pytest fixtures
│   ├── test_discovery.py # discovery tests
│   ├── test_manager.py   # manager tests
│   └── test_cache.py     # cache tests
├── .pi/
│   └── mcp.json          # Config Pi
├── memory-bank/           # Documentação
├── pyproject.toml
├── README.md
└── uv.lock
```

### 2025-10-06 (Final)
- **Fase 7 (T-060, T-061, T-062)**: Suite de testes pytest implementada
  - 27 testes cobrindo discovery, cache, manager, circuit breaker
  - Dependências: pytest, pytest-asyncio, pytest-mock
  - Todos os testes passando

**Status Final: ✅ PROJETO COMPLETO**

### 2025-10-06 (Pi Integration)
- MCP configurado e funcionando no Pi
- Servidor registrado via `pi mcp add -l searxng-web-search`
- Tool `web_search` disponível
- Correção das assinaturas dos handlers MCP

### 2025-10-06 (Debug - RESOLVIDO)
- **Problema:** `Invalid request parameters` ao chamar web_search via Pi
- **Causa:** API antiga do MCP SDK incompatível com protocolo moderno do Pi
- **Solução:** Migrou de `mcp[cli]>=1.0.0` para `fastmcp>=4.0.0`
- **Código novo:** Usa decorator `@mcp.tool()` em vez de `add_request_handler`
- **Commit:** `0822031` no branch `fix/fastmcp-migration`
- **Testes:** 27 testes passando ✅
- **Pi:** Ferramenta funcionando corretamente via `mcp__searxng_web_search__web_search`
