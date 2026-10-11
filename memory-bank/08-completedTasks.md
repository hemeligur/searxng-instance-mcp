# Completed Tasks

Tarefas concluídas do projeto, ordenadas por código.

---

## Configuração (CFG)

### CFG-001: Configuração via mcp.json e Environment Variables
- **Data de Conclusão**: 2025-10-07
- **Entregáveis**:
  - `SEARXNG_DISABLED_INSTANCES` - lista de URLs separadas por vírgula
  - `SEARXNG_DEBUG_TOOLS` - habilitar/desabilitar tools de debug (default: false)
  - `SEARXNG_BACKOFF_BASE` e `SEARXNG_BACKOFF_MAX`
  - Tools de debug desabilitadas por padrão, habilitadas via config
  - Filtragem de instâncias desabilitadas no manager
  - Não persistir instâncias explicitamente desabilitadas
- **Arquivos Alterados**:
  - `src/searxng_mcp/constants.py` - +env var config helpers
  - `src/searxng_mcp/models.py` - +disabled field
  - `src/searxng_mcp/server.py` - +conditional debug tools
  - `src/searxng_mcp/manager.py` - +disabled filtering
  - `src/searxng_mcp/persistence.py` - +filter disabled
  - `memory-bank/04-techContext.md` - +env vars docs
  - `README.md` - +config section
- **Testes**: 19 novos testes em `tests/test_config.py`
- **Resultado**: 57 testes passando ✅

### CFG-002: Discovery Dinâmico Corrigido
- **Data de Conclusão**: 2025-10-07
- **Problema**: API do searx.space `/api/v1/instances` retornava 404
- **Entregáveis**:
  - Endpoint corrigido: `https://searx.space/data/instances.json`
  - Fallback para GitHub: `purujawa06-bot/SearXNG-active-instance`
  - Lista expandida: 13 instâncias fallback (antes: 3-4)
  - Discovery retorna até 20 instâncias filtradas do searx.space
- **Arquivos Alterados**:
  - `src/searxng_mcp/discovery.py` - endpoint, GitHub fallback, lista expandida
  - `src/searxng_mcp/models.py` - `from_api_response()` atualizado para novo formato
  - `tests/test_discovery.py` - +testes para GitHub fallback
  - `tests/conftest.py` - fixture atualizada
- **Testes**: 60 testes passando ✅

---

## Fase 1: Estrutura Base

### T-001: Criar `pyproject.toml` com dependências
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: `pyproject.toml` com `fastmcp`, `httpx`, `tenacity`

### T-002: Criar estrutura de diretórios `src/searxng_mcp/`
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: Estrutura de diretórios criada

### T-003: Criar `src/searxng_mcp/__init__.py` exportando servidor
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: Módulo importável

### T-004: Criar `src/searxng_mcp/models.py` com dataclasses
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: CircuitState, SearchResult dataclasses

---

## Fase 2: Discovery Dinâmico

### T-010: Implementar `InstanceDiscovery` em `discovery.py`
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: Módulo `discovery.py` funcional
- **Detalhes**:
  - Busca instâncias de `https://searx.space/api/v1/instances`
  - Cache local em `~/.cache/searxng-mcp/instances.json`
  - TTL configurável

### T-011: Definir `FALLBACK_INSTANCES` hardcoded
- **Data de Conclusão**: 2025-10-05
- **Entregáveis**: Lista de instâncias fallback em `constants.py`

---

## Fase 3: Gerenciamento de Pool

### T-020: Implementar `SearXNGManager` em `manager.py`
- **Data de Conclusão**: 2025-10-06 (Madrugada)
- **Entregáveis**: Módulo `manager.py` funcional
- **Detalhes**:
  - Circuit breaker: CLOSED → OPEN → HALF_OPEN
  - TTL: 5 minutos
  - Fallback automático entre instâncias

---

## Fase 4: Servidor MCP

### T-030: Implementar `server.py` com SDK MCP
- **Data de Conclusão**: 2025-10-06 (Madrugada)
- **Entregáveis**: Servidor FastMCP exposto
- **Histórico**: Originalmente com `mcp[cli]`, migrado para `fastmcp>=4.0.0`

### T-031: Implementar `main()` com initialization do servidor
- **Data de Conclusão**: 2025-10-06 (Madrugada)
- **Entregáveis**: Entry point funcional

---

## Fase 5: Configuração Pi

### T-040: Criar `.pi/mcp.json` com configuração do servidor
- **Data de Conclusão**: 2025-10-06 (Manhã)
- **Entregáveis**: Configuração para Pi Agent
- **Nota**: Posteriormente movido para registro global

### T-041: Documentar comando de registro
- **Data de Conclusão**: 2025-10-06 (Manhã)
- **Entregáveis**: Documentação de configuração

---

## Fase 6: Documentação

### T-050: Criar `README.md`
- **Data de Conclusão**: 2025-10-06 (Manhã)
- **Entregáveis**: `README.md` completo com:
  - Instalação (`uv sync`)
  - Uso da ferramenta `web_search`
  - Configuração de instâncias
  - Variáveis de ambiente
  - Troubleshooting

---

## Fase 7: Testes

### T-060: Teste de conexão com instância
- **Data de Conclusão**: 2025-10-06
- **Entregáveis**: Testes em `tests/test_discovery.py`

### T-061: Teste de fallback
- **Data de Conclusão**: 2025-10-06
- **Entregáveis**: Testes em `tests/test_manager.py`

### T-062: Teste de cache de instâncias
- **Data de Conclusão**: 2025-10-06
- **Entregáveis**: Testes em `tests/test_cache.py`

---

## Melhorias de Documentação

### DOC-001: Clarificar propósito do MCP (2025-10-06)
- **Data de Conclusão**: 2025-10-06
- **Problema**: README não deixava claro que o MCP é um cliente que usa instâncias públicas online, não um servidor de instâncias locais
- **Entregáveis**:
  - **README.md reescrito**: Nova seção "Como Funciona" com diagrama no topo, nota de destaque sobre instâncias públicas
  - **`docs/searxng-local.md` criado**: Documentação para quem quer rodar instância local com Docker
- **Resultado**: Usuários entendem claramente o propósito e diferenças

---

## Correções Importantes

### FIX-001: Classifier de Licença Inválido (2025-10-06)
- **Problema**: `ValueError: Unknown classifier` ao fazer `uv pip install` ou `uv build`
- **Causa Raiz**: Classifier `"License :: OSI Approved :: GNU General Public License v3.0"` não existe na lista oficial de Trove Classifiers
- **Solução**: Corrigido para `"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"`
- **Arquivo**: `pyproject.toml` linha 10
- **Verificação**: Build passou com sucesso (`uv build`)
- **Nota**: Conforme PEP 639, classifiers de licença estão deprecated. Preferir `license` em `project`.

### Fix FastMCP (2025-10-06)
- **Problema**: API antiga do MCP SDK incompatível com protocolo moderno do Pi
- **Solução**: Migrou de `mcp[cli]>=1.0.0` para `fastmcp>=4.0.0`
- **Commits**: `0822031` (fix), `5716722` (merge PR #1)
- **Issue**: `Invalid request parameters` ao chamar via Pi

---

## Sistema de Tiering Híbrido (EPD-002)

### TIER-001: Criar dataclass ExternalMetrics
- **Data de Conclusão**: 2025-01-19
- **Entregáveis**:
  - `ExternalMetrics` dataclass em `models.py`
  - Campos: `uptime_day`, `uptime_week`, `tls_grade`, `engine_count`, `error_load`, `error_check`, `network_country`, `last_updated`
  - Métodos `to_dict()` e `from_dict()` para serialização
- **Arquivos Alterados**: `src/searxng_mcp/models.py`
- **Testes**: Verificados manualmente, 68 testes passando ✅

### TIER-002: Estender DiscoveredInstance com novos campos da API
- **Data de Conclusão**: 2025-01-19
- **Entregáveis**:
  - Campos adicionais: `error_load`, `error_check`, `network_country`, `network_region`, `uptime_week`
  - Parser `from_api_response()` atualizado para extrair novos campos
- **Arquivos Alterados**: `src/searxng_mcp/models.py`, `tests/conftest.py`
- **Testes**: 68 testes passando ✅

### TIER-003: Estender InstanceStatus com métricas internas
- **Data de Conclusão**: 2025-01-19
- **Entregáveis**:
  - Campos: `total_requests`, `successful_requests`, `response_times_ms`
  - Método `record_request(success, response_time_ms)`
  - Property `success_rate` (retorna 0.5 se sem histórico)
  - Campos internos `_external_metrics` e `_last_external_update`
  - Métodos `to_dict()` e `from_dict()` atualizados com serialização completa
- **Arquivos Alterados**: `src/searxng_mcp/models.py`
- **Testes**: 68 testes passando ✅

### TIER-004: Implementar cálculo de score híbrido (parcial)
- **Data de Conclusão**: 2025-01-19
- **Entregáveis**:
  - `RECENCY_HALF_LIFE = 3600.0` segundos
  - `_calculate_recency_bonus()` com decay exponencial (0.5 + 0.5 * decay)
  - Property `circuit_score` (CLOSED=1.0, HALF_OPEN=0.5, OPEN=0.0)
  - `calculate_tier_score()`: Score = 40% External + 60% Internal
  - `get_tier()`: T1≥0.70, T2≥0.45, T3<0.45
- **Pesos Implementados**:
  - External: uptime(20%) + tls(15%) + engines(5%) = 40%
  - Internal: success_rate(35%) + recency(15%) + circuit(10%) = 60%
- **Scores de Referência**:
  | Cenário | Score | Tier |
  |---------|-------|------|
  | Nova + TLS A+ + 100% uptime | ~0.75 | T1 |
  | 4/4 requests + TLS A+ | ~1.00 | T1 |
  | 10/10 requests (sem ext) | ~0.60 | T2 |
  | TLS B + 10/10 | ~0.76 | T1 |
- **Testes**: 68 testes passando ✅

---

## Resumo de Entregas

| Fase | Tarefas | Status |
|------|---------|--------|
| Fase 1: Estrutura Base | T-001 a T-004 | ✅ 4/4 |
| Fase 2: Discovery | T-010, T-011 | ✅ 2/2 |
| Fase 3: Pool Manager | T-020 | ✅ 1/1 |
| Fase 4: Servidor MCP | T-030, T-031 | ✅ 2/2 |
| Fase 5: Config Pi | T-040, T-041 | ✅ 2/2 |
| Fase 6: Documentação | T-050 | ✅ 1/1 |
| Fase 7: Testes | T-060 a T-062 | ✅ 3/3 |
| Melhorias Documentação | DOC-001 | ✅ 1/1 |
| Sistema Tiering | TIER-001 a TIER-004 | ✅ 4/4 |
| **Total** | **18 tarefas** | **✅ 18/18** |
