# Tasks

## Backlog

Este arquivo contém apenas tarefas pendentes. Tarefas concluídas foram movidas para `08-completedTasks.md`.

---

## Tarefas Pendentes

### TIER-006: Modificar manager.search() para usar tiers

**Data de Criação**: 2025-01-19

**Status**: [ ] Pendente

**Prioridade**: Alta

**Resumo**: Alterar lógica de seleção de instâncias para usar tiers

**Entregáveis**: 
- Busca tenta instâncias na ordem T1 → T2 → T3
- Shuffle dentro de cada tier
- Degradação graceful: T2 assume se T1 vazio/falhou

**Contexto**: Ponto de entrada para todas as buscas - precisa usar o novo sistema de scoring

**Critérios de Aceitação**: 
- Instâncias T1 tentadas primeiro
- Fallback automático para T2/T3
- Métricas atualizadas após cada tentativa via `record_request()`

**Subtarefas**:
- [ ] Organizar instâncias por tier usando `get_tier()`
- [ ] Implementar shuffle dentro de cada tier
- [ ] Loop principal: T1 → T2 → T3
- [ ] Registrar sucesso/falha após cada tentativa

---

### TIER-008: Implementar testes unitários para scoring

**Data de Criação**: 2025-01-19

**Status**: [ ] Pendente

**Prioridade**: Alta

**Resumo**: Testar todos os componentes do sistema de tiers

**Entregáveis**: 
- Testes para `ExternalMetrics`
- Testes para `calculate_tier_score()`
- Testes para `_calculate_recency_bonus()`
- Testes de integração para tiers no manager

**Contexto**: Garantir qualidade e permitir refatoração segura

**Critérios de Aceitação**: 
- 100% coverage nos novos métodos
- Testes de edge cases (sem dados externos, recency zero, etc)

**Subtarefas**:
- [ ] Testar `test_hybrid_score_with_external_data`
- [ ] Testar `test_tls_grades_affect_score`
- [ ] Testar `test_recency_decay`
- [ ] Testar `test_tier_classification`
- [ ] Testar `test_tier_selection_order`
- [ ] Testar `test_shuffle_within_tier`
- [ ] Testar `test_graceful_degradation`

---

## Notas

- Tarefas concluídas foram movidas para `08-completedTasks.md`.
- **TIER-001 a TIER-005**: ✅ Implementados
- **TIER-006, TIER-008**: Pendentes
- Para histórico completo, consulte `08-completedTasks.md`.
