# Tasks

## Backlog

Este arquivo contém apenas tarefas pendentes. Tarefas concluídas foram movidas para `08-completedTasks.md`.

---

## Tarefas Pendentes

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

- Tarefas concluídas foram movidas para `08-completedTasks.md`.
- CFG-001: ✅ Implementada - Configuração via env vars
- Para histórico completo, consulte `08-completedTasks.md`.
