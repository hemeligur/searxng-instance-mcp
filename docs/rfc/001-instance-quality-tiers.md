# RFC-001: Sistema de Tiering por Qualidade de Instâncias

**Status**: Proposto  
**Data**: 2025-10-07  
**Autor**: hemeligur  

---

## Resumo

Implementar um sistema de pontuação para classificar instâncias SearXNG em **3 tiers de qualidade**, priorizando instâncias com melhor histórico de sucesso.

---

## Contexto

### Problema Atual

O sistema atual:
1. Faz shuffle das instâncias apenas na **inicialização** do servidor
2. Usa a **mesma ordem** para todas as buscas subsequentes
3. Só considera `failure_count` e `circuit_state` (sem métricas históricas)
4. Primeira instância "boa" é sempre a mesma até restart

### Resultado

Uma instância pode se tornar a "preferida" sem motivo - apenas porque foi a primeira no shuffle.

---

## Proposta

### Sistema de Pontuação

Classificar cada instância em um **tier** baseado em score calculado:

```
score = (success_rate × 0.4) + 
         (recency_bonus × 0.3) + 
         (circuit_score × 0.2) +
         (failure_penalty × 0.1)
```

#### Componentes do Score

| Componente | Peso | Descrição |
|------------|------|-----------|
| `success_rate` | 40% | `successful_requests / total_requests` |
| `recency_bonus` | 30% | Bonus por sucesso recente |
| `circuit_score` | 20% | CLOSED=1.0, HALF_OPEN=0.5, OPEN=0.0 |
| `failure_penalty` | 10% | Penalidade por falhas consecutivas |

### Definição de Tiers

| Tier | Score | Nome | Comportamento |
|------|-------|------|---------------|
| **T1** | ≥ 0.75 | Premium | Prioridade máxima, tentar primeiro |
| **T2** | 0.40-0.74 | Standard | Fallback principal |
| **T3** | < 0.40 | Risky | Último recurso |

---

## Fluxo de Seleção Proposto

```
search(query)
    │
    ├─► T1 (Premium) → shuffle → try [A, C, E] → success? → return
    │
    ├─► T2 (Standard) → shuffle → try [B, D, F] → success? → return
    │
    └─► T3 (Risky) → shuffle → try [G, H, I] → success? → return
                                                    │
                                                    ▼
                                              ❌ Error
```

---

## Campos a Adicionar em `InstanceStatus`

```python
@dataclass
class InstanceStatus:
    # ... existente ...
    
    # Novos campos para métricas
    total_requests: int = 0
    successful_requests: int = 0
    response_times_ms: list[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.5  # Neutro sem histórico
        return self.successful_requests / self.total_requests
    
    def calculate_tier_score(self) -> float:
        """Calcula score para classificação em tier."""
        # Implementação da fórmula acima
        ...
    
    def get_tier(self) -> int:
        """Retorna tier (1=Premium, 2=Standard, 3=Risky)."""
        score = self.calculate_tier_score()
        if score >= 0.75:
            return 1
        elif score >= 0.40:
            return 2
        return 3
```

### Atualização de Métricas

```python
def record_request(self, success: bool, response_time_ms: float = None):
    """Registra resultado de uma requisição."""
    self.total_requests += 1
    if success:
        self.successful_requests += 1
        self.last_success = time.time()
    if response_time_ms is not None:
        self.response_times_ms.append(response_time_ms)
        self.response_times_ms = self.response_times_ms[-10:]
```

---

## Implementação em `manager.py`

```python
async def search(self, query: str, limit: int) -> SearchResponse:
    # Organiza instâncias por tier
    tiers = {1: [], 2: [], 3: []}
    
    for url, status in self.instances.items():
        if status.is_available():
            tier = status.get_tier()
            tiers[tier].append(url)
    
    # Shuffle dentro de cada tier (para distribuição de carga)
    for tier_urls in tiers.values():
        random.shuffle(tier_urls)
    
    # Tenta na ordem: T1 → T2 → T3
    errors = []
    
    for tier in [1, 2, 3]:
        for url in tiers[tier]:
            result = await self._try_instance(url, query, limit)
            
            if result.success:
                # Atualiza métricas
                status = self.instances[url]
                status.record_request(success=True, response_time_ms=result.response_time_ms)
                return result
            else:
                errors.append({"instance": url, "error": result.error})
                self.instances[url].record_request(success=False)
    
    # Todas falharam
    return error_response(errors)
```

---

## Critérios de Aceitação

- [ ] Instâncias classificadas em 3 tiers baseados em score
- [ ] Shuffle feito dentro de cada tier (não global)
- [ ] Busca tenta T1 → T2 → T3 em ordem
- [ ] Métricas (`total_requests`, `successful_requests`) atualizadas após cada requisição
- [ ] Score recalculado após cada requisição
- [ ] Instâncias novas começam com score neutro (0.5)
- [ ] Degradação graceful: T2 assume se T1 vazio/falhou
- [ ] Persistência do novo estado

---

## Testes Propostos

```python
def test_tier_classification():
    """Instâncias com alto success_rate são T1."""
    ...

def test_tier_selection_order():
    """Tenta T1 antes de T2."""
    ...

def test_shuffle_within_tier():
    """Instâncias do mesmo tier são embaralhadas."""
    ...

def test_graceful_degradation():
    """Se T1 vazio, usa T2."""
    ...
```

---

## Alternativas Consideradas

### Weighted Random Selection

Em vez de tiers fixos, usar probabilidade proporcional ao score:

```python
def weighted_random_select(instances):
    scores = [calc_score(i) for i in instances]
    total = sum(scores)
    probs = [s/total for s in scores]
    return random.choices(instances, weights=probs)[0]
```

**Prós**: Mais suave, não há "corte" abrupto  
**Contras**: Menos determinístico, harder to debug

### Decisão: Manter Tiers

A abordagem de tiers foi escolhida por:
1. Simplicidade de debug (ordem clara)
2. Comportamento previsível
3. Fácil de monitorar (métricas por tier)

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| T1 vazio após falhas | Sistema degrada para T2 automaticamente |
| Bias de sobrevivência | Métricas de recência evitam fixação |
| Overhead de cálculo | Score calculado apenas quando necessário |

---

## Timeline Sugerido

1. **Fase 1**: Adicionar campos de métricas em `InstanceStatus`
2. **Fase 2**: Implementar cálculo de score e tier
3. **Fase 3**: Modificar `search()` para usar tiers
4. **Fase 4**: Atualizar persistência
5. **Fase 5**: Testes e documentação

---

## Referências

- [Circuit Breaker Pattern](docs/developer/arquitetura.md)
- [Issue #5](https://github.com/hemeligur/searxng-instance-mcp/issues/5) (criar após merge)

---

## Status History

| Data | Status | Notas |
|------|--------|-------|
| 2025-10-07 | Proposto | RFC criado |
