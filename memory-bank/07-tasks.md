# Tasks

## Backlog

Este arquivo contém apenas tarefas pendentes. Tarefas concluídas foram movidas para `08-completedTasks.md`.

---

## Tarefas Pendentes

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
- **TIER-001 a TIER-006**: ✅ Implementados
- **TIER-008**: Pendente
- Para histórico completo, consulte `08-completedTasks.md`.
