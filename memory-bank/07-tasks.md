# Tasks

## Backlog

Este arquivo contém apenas tarefas pendentes. Tarefas concluídas foram movidas para `08-completedTasks.md`.

---

## Tarefas Pendentes

### CFG-001: Configuração via mcp.json e Environment Variables

**Data de Criação**: 2025-10-07

**Status**: [ ] Pendente

**Prioridade**: Alta

**Resumo**: Implementar configuração via environment variables no mcp.json para instâncias desabilitadas e tools de debug.

**Entregáveis**:
- Configuração `SEARXNG_DISABLED_INSTANCES` - lista de URLs separadas por vírgula
- Configuração `SEARXNG_DEBUG_TOOLS` - habilitar/desabilitar tools de debug (default: false)
- Configuração `SEARXNG_BACKOFF_BASE` e `SEARXNG_BACKOFF_MAX`
- Tools de debug desabilitadas por padrão, habilitadas via config
- Filtragem de instâncias desabilitadas no manager
- Não persistir instâncias explicitamente desabilitadas

**Contexto**: Issue #4 revelou necessidade de poder desabilitar instâncias permanentemente (ex: search.ctq.ro com anti-bot). Usuário não quer novas tools visíveis - debug tools devem ser opt-in via config.

**Critérios de Aceitação**:
- Instâncias em `SEARXNG_DISABLED_INSTANCES` não são usadas em buscas
- `SEARXNG_DEBUG_TOOLS=false` não registra as 3 tools de status (default)
- `SEARXNG_DEBUG_TOOLS=true` registra tools de debug
- Config via env vars funciona com mcp.json

**Subtarefas**:
- [ ] Modificar `server.py` para ler env vars e conditionally registrar debug tools
- [ ] Modificar `manager.py` para filtrar instâncias desabilitadas
- [ ] Modificar `persistence.py` para não persistir instâncias desabilitadas
- [ ] Testar configuração via mcp.json
- [ ] Atualizar documentação

**Notas**: Relacionado à issue #4 - rate limiting detection

---

### CFG-002: Investigar e Corrigir Discovery Dinâmico

**Data de Criação**: 2025-10-07

**Status**: [ ] Pendente

**Prioridade**: Média

**Resumo**: A API do searx.space está retornando 404. Necessário investigar alternativas para discovery dinâmico de instâncias públicas.

**Entregáveis**:
- Identificar endpoint funcional para discovery de instâncias
- Ou implementar lista fallback mais robusta (~10 instâncias verificadas)
- Cache inteligente com refresh periódico

**Contexto**: Issue sobre distribuição de carga revelou que apenas 3 fallback instances são usadas. Discovery dinâmico não funciona (API retornando 404).

**Critérios de Aceitação**:
- Discovery retorna instâncias públicas funcionais
- Ou fallback pool contém ≥10 instâncias verificadas
- Sistema usa mais instâncias quando disponível

**Subtarefas**:
- [ ] Investigar APIs alternativas (searxng.site, etc)
- [ ] Testar endpoints conhecidos
- [ ] Se não encontrar API funcional, expandir fallback list
- [ ] Implementar refresh periódico de instâncias

**Notas**: API testada: `searx.space/api/v1/instances` (404), `searxng.site/api/instances` (rate limit), `searxng.org/api/v1/instances` (404)

---

## Notas

- Todas as tarefas do backlog foram concluídas.
- Para histórico completo, consulte `08-completedTasks.md`.
