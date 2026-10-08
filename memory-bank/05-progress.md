# Progress

## Status Geral
🟢 **PRODUTO PRONTO** - Servidor MCP funcionando globalmente no Pi

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
  - pytest>=9.1.1, pytest-asyncio>=1.4.0, pytest-mock>=3.16.0 adicionados ao pyproject.toml

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
- **T-030, T-031**: Implementado servidor MCP (posteriormente migrado para FastMCP)
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
  - `pyproject.toml` com dependências (fastmcp, httpx, tenacity)
  - `src/searxng_mcp/` com `__init__.py`, `models.py`, `server.py`
  - README.md criado
  - Dependências instaladas via `uv sync`

### 2025-10-06 (Final - COMPLETO)
- **Fase 7 (T-060, T-061, T-062)**: Suite de testes pytest implementada
  - 27 testes cobrindo discovery, cache, manager, circuit breaker
  - Dependências: pytest, pytest-asyncio, pytest-mock
  - Todos os testes passando

### 2025-10-06 (MCP Bug Fix - RESOLVIDO)
- **Problema:** `Invalid request parameters` ao chamar web_search via Pi
- **Causa:** API antiga do MCP SDK incompatível com protocolo moderno do Pi
- **Solução:** Migrou de `mcp[cli]>=1.0.0` para `fastmcp>=4.0.0`
- **Código novo:** Usa decorator `@mcp.tool()` em vez de `add_request_handler`
- **Branch:** `fix/fastmcp-migration`
- **PR:** #1 mesclado na main
- **Commit merge:** `5716722`
- **Testes:** 27 testes passando ✅

### 2025-10-06 (Global Setup)
- Servidor registrado globalmente em `/home/guilherme/.pi/agent/mcp.json`
- Exposure: `direct`
- Configuração local `.pi/mcp.json` removida
- Tool disponível via: `mcp__searxng_web_search__web_search`

### 2025-10-06 (Documentação)
- **Skill document-system executada**
- **Documentação criada:**
  - `docs/developer/arquitetura.md` - Documentação técnica completa com diagramas
  - `docs/usuario/troubleshooting.md` - Guia de troubleshooting com problemas comuns
- **README.md atualizado:**
  - Seção de documentação reestruturada
  - Links para docs/ adicionados
  - Quick Start adicionado
  - Seção de troubleshooting referenciando docs/

### 2025-10-06 (Reorganização de Docs)
- **Docs movidos da raiz para docs/:**
  - `SearXNG-Busca-Web.md` → `docs/usuario/searxng-guide.md`
  - `searxng-skill.md` → `docs/skill/searxng-skill.md`
- **Diretórios criados:** `docs/usuario/`, `docs/developer/`, `docs/skill/`
- **README.md atualizado com novos caminhos de links**
- **Memory Bank atualizado:**
  - 06-activeContext.md atualizado com nova estrutura
  - 05-progress.md atualizado com reorganização

### 2025-10-06 (Build Fix)
- **Problema**: `ValueError: Unknown classifier in field 'project.classifiers'`
- **Causa**: Classifier de licença inválido: `GNU General Public License v3.0`
- **Solução**: Corrigido para `GNU General Public License v3 (GPLv3)` (formato oficial Trove)
- **Arquivo**: `pyproject.toml`
- **Build**: Verificada com sucesso (`uv build`)

### 2025-10-07 (CFG-001 - Config via Env Vars)
- **Tarefa**: Configuração via environment variables para instâncias desabilitadas e tools de debug
- **Entregáveis implementados**:
  - `SEARXNG_DISABLED_INSTANCES` - URLs separadas por vírgula
  - `SEARXNG_DEBUG_TOOLS` - true/false para tools de status
  - `SEARXNG_BACKOFF_BASE` e `SEARXNG_BACKOFF_MAX` - configuração de backoff
- **Arquivos alterados**:
  - `constants.py` - helpers: `get_disabled_instances()`, `is_debug_enabled()`, etc.
  - `models.py` - campo `disabled` no `InstanceStatus`
  - `server.py` - registro condicional de debug tools
  - `manager.py` - filtragem de instâncias desabilitadas
  - `persistence.py` - não persiste instâncias desabilitadas
- **Testes**: 19 novos testes em `tests/test_config.py`
- **Testes totais**: 57 passando ✅
