# EPD-002: Sistema de Tiering por Qualidade de Instâncias

**Status**: Draft  
**Data**: 2025-01-19  
**Autor**: hemeligur  
**Revisor**: Sugestão de melhoria - integrar métricas externas da API searx.space

---

## Resumo

Implementar um sistema de pontuação **híbrido** para classificar instâncias SearXNG em **3 tiers de qualidade**, combinando:
1. **Dados externos** da API searx.space (uptime, TLS, engines)
2. **Métricas locais** inferidas运行时 (success_rate, circuit_state, recency)

---

## Contexto

### Problema Atual (EPD Original)

O EPD original propunha um score **puramente inferido/calculado** com 4 componentes:
- `success_rate` (40%)
- `recency_bonus` (30%)
- `circuit_score` (20%)
- `failure_penalty` (10%)

**Problema identificado**: Ignora completamente os dados externos já disponíveis da API `searx.space/data/instances.json`.

### Dados Externos Já Disponíveis

A API searx.space fornece métricas ricas que não estão sendo utilizadas:

```json
{
  "https://sx.xo.st": {
    "uptime": {"uptimeDay": 100.0, "uptimeWeek": 99.8},
    "tls": {"grade": "A+"},
    "engines": {"google": {}, "bing": {}, "duckduckgo": {}},
    "network": {"country": "DE", "region": "..."},
    "error_load": 0.0,
    "error_check": 0.0
  }
}
```

### Proposta de Score Híbrido

**Score = ScoreExterno(40%) + ScoreInterno(60%)**

#### Componente Externo (40%)

| Métrica | Peso | Fonte | Normalização |
|---------|------|-------|--------------|
| `uptime_score` | 20% | `uptime.uptimeDay` | `uptime / 100` |
| `tls_score` | 15% | `tls.grade` | A+=1.0, A=0.9, B=0.7, C=0.5, D=0.3, E=0.1 |
| `engine_diversity` | 5% | `len(engines)` | `min(count / 20, 1.0)` |

#### Componente Interno (60%)

| Métrica | Peso | Descrição |
|---------|------|-----------|
| `success_rate` | 35% | `successful_requests / total_requests` |
| `recency_bonus` | 15% | Bonus por sucesso recente (decay exponencial) |
| `circuit_score` | 10% | CLOSED=1.0, HALF_OPEN=0.5, OPEN=0.0 |

### Fórmula Final

```python
def calculate_tier_score(self) -> float:
    """Calcula score híbrido para classificação em tier."""
    
    # Componente Externo (40%)
    external = 0.0
    if self._external_metrics:
        uptime_score = self._external_metrics.uptime_day / 100.0
        tls_scores = {"A+": 1.0, "A": 0.9, "B": 0.7, "C": 0.5, "D": 0.3, "E": 0.1}
        tls_score = tls_scores.get(self._external_metrics.tls_grade, 0.3)
        engine_score = min(self._external_metrics.engine_count / 20.0, 1.0)
        
        external_raw = uptime_score*0.20 + tls_score*0.15 + engine_score*0.05
        external = (external_raw / 0.40) * 0.4  # Normalizado para máx 0.4
    else:
        external = 0.0  # Sem contribuição
    
    # Componente Interno (60%)
    internal_raw = (
        self.success_rate * 0.35 +
        self._calculate_recency_bonus() * 0.15 +
        self.circuit_score * 0.10
    )
    internal = (internal_raw / 0.60) * 0.6  # Normalizado para máx 0.6
    
    return external + internal
```

### Scores de Referência (Implementados)

| Cenário | Score | Tier |
|---------|-------|------|
| Nova + TLS A+ + 100% uptime | ~0.75 | T1 |
| 4/4 requests + TLS A+ | ~1.00 | T1 |
| 10/10 requests (sem ext) | ~0.60 | T2 |
| 1/3 success + TLS A+ | ~0.77 | T1 |
| TLS B + 10/10 | ~0.76 | T1 |

### Definição de Tiers

| Tier | Score | Nome | Comportamento |
|------|-------|------|---------------|
| **T1** | ≥ 0.70 | Premium | Prioridade máxima, tentar primeiro |
| **T2** | 0.45-0.69 | Standard | Fallback principal |
| **T3** | < 0.45 | Risky | Último recurso |

---

## Fluxo de Seleção Proposto

```
search(query)
    │
    ├─► T1 (Good) → shuffle → try [A, C, E] → success? → return
    │
    ├─► T2 (Standard) → shuffle → try [B, D, F] → success? → return
    │
    └─► T3 (Risky) → shuffle → try [G, H, I] → success? → return
                                                    │
                                                    ▼
                                              ❌ Error
```

---

## Modelo de Dados

### Extensão do `InstanceStatus`

```python
@dataclass
class ExternalMetrics:
    """Dados externos da API searx.space."""
    uptime_day: float = 0.0
    uptime_week: float = 0.0
    tls_grade: str = "C"
    engine_count: int = 0
    error_load: float = 0.0
    error_check: float = 0.0
    network_country: str = ""


@dataclass
class InstanceStatus:
    # ... campos existentes ...
    
    # Novos campos para métricas internas
    total_requests: int = 0
    successful_requests: int = 0
    response_times_ms: list[float] = field(default_factory=list)
    
    # Cache de métricas externas (atualizado a cada discovery)
    _external_metrics: Optional[ExternalMetrics] = field(default=None, repr=False)
    _last_external_update: Optional[float] = field(default=None, repr=False)
    
    # RECENCY_DECAY: half-life de 1 hora
    RECENCY_HALF_LIFE = 3600.0  # segundos
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.5  # Neutro sem histórico
        return self.successful_requests / self.total_requests
    
    @property
    def circuit_score(self) -> float:
        """Score baseado no estado do circuit breaker."""
        return {
            CircuitState.CLOSED: 1.0,
            CircuitState.HALF_OPEN: 0.5,
            CircuitState.OPEN: 0.0,
        }.get(self.state, 0.0)
    
    def _calculate_recency_bonus(self) -> float:
        """Calcula bonus de recência com decay exponencial.
        
        Retorna valor entre 0.0 e 1.0 baseado em quão recente foi o último sucesso.
        """
        if self.last_success is None:
            return 0.5  # Neutro sem dados
        
        import time
        elapsed = time.time() - self.last_success
        
        # Decay exponencial: score = 0.5 * (0.5 ^ (elapsed / half_life))
        # + 0.5 para não ir abaixo de 0.5
        decay = 0.5 ** (elapsed / self.RECENCY_HALF_LIFE)
        return 0.5 + (0.5 * decay)
    
    def calculate_tier_score(self) -> float:
        """Calcula score híbrido para classificação em tier."""
        # Componente Externo (50%)
        external = 0.0
        if self._external_metrics:
            uptime_score = self._external_metrics.uptime_day / 100.0
            tls_scores = {"A+": 1.0, "A": 0.9, "B": 0.7, "C": 0.5, "D": 0.3, "E": 0.1}
            tls_score = tls_scores.get(self._external_metrics.tls_grade, 0.3)
            engine_score = min(self._external_metrics.engine_count / 20.0, 1.0)
            
            external = (
                uptime_score * 0.30 +
                tls_score * 0.15 +
                engine_score * 0.05
            )
        else:
            external = 0.3  # Penalidade
        
        # Componente Interno (50%)
        internal = (
            self.success_rate * 0.25 +
            self._calculate_recency_bonus() * 0.15 +
            self.circuit_score * 0.10
        )
        
        return (external * 0.5) + (internal * 0.5)
    
    def get_tier(self) -> int:
        """Retorna tier (1=Premium, 2=Standard, 3=Risky)."""
        score = self.calculate_tier_score()
        if score >= 0.70:  # Ajustado de 0.75 para 0.70
            return 1
        elif score >= 0.45:  # Ajustado de 0.40 para 0.45
            return 2
        return 3

    def update_external_metrics(self, metrics: ExternalMetrics) -> None:
        """Atualiza métricas externas da API searx.space."""
        import time
        self._external_metrics = metrics
        self._last_external_update = time.time()

    def record_request(self, success: bool, response_time_ms: float = None):
        """Registra resultado de uma requisição."""
        import time
        
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.last_success = time.time()
        if response_time_ms is not None:
            self.response_times_ms.append(response_time_ms)
            self.response_times_ms = self.response_times_ms[-10:]
```

### Extensão do `DiscoveredInstance`

```python
@dataclass
class DiscoveredInstance:
    # ... existente ...
    
    # Novos campos da API searx.space
    error_load: float = 0.0
    error_check: float = 0.0
    network_country: str = ""
    
    @classmethod
    def from_api_response(cls, url: str, data: dict) -> "DiscoveredInstance":
        # ... código existente ...
        
        # Novos campos
        error_load = data.get("error_load", 0.0)
        error_check = data.get("error_check", 0.0)
        network = data.get("network", {})
        network_country = network.get("country", "") if network else ""
        
        return cls(
            # ... campos existentes ...
            error_load=error_load,
            error_check=error_check,
            network_country=network_country,
        )
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

## Fluxo de Integração com Discovery

```python
async def discover_instances(use_cache: bool = True) -> dict[str, InstanceStatus]:
    """Descobre instâncias e retorna com métricas externas.
    
    Returns:
        Dict de URL -> InstanceStatus com _external_metrics preenchidas.
    """
    # ... fetch da API searx.space ...
    
    for url, instance_data in instances_data.items():
        discovered = DiscoveredInstance.from_api_response(url, instance_data)
        
        # Criar ou atualizar InstanceStatus
        if url not in instances:
            instances[url] = InstanceStatus(url=url)
        
        # Atualizar métricas externas
        instances[url].update_external_metrics(ExternalMetrics(
            uptime_day=discovered.uptime,
            tls_grade=discovered.tls_rank,
            engine_count=len(discovered.engines),
            error_load=discovered.error_load,
            error_check=discovered.error_check,
            network_country=discovered.network_country,
        ))
    
    return instances
```

---

## Critérios de Aceitação Atualizados

- [ ] Score híbrido: 50% externo (searx.space) + 50% interno (runtime)
- [ ] Campos `ExternalMetrics` em `InstanceStatus`
- [ ] Uptime da API usado no cálculo (peso 30%)
- [ ] TLS grade usado no cálculo (peso 15%)
- [ ] Engine count usado no cálculo (peso 5%)
- [ ] Métricas externas atualizadas a cada ciclo de discovery
- [ ] Instâncias sem dados externos recebem score penalizado (0.3)
- [ ] Recency bonus com decay exponencial (half-life 1h)
- [ ] Thresholds ajustados: T1 ≥ 0.70, T2 ≥ 0.45

---

## Testes Propostos

```python
def test_hybrid_score_with_external_data():
    """Score é maior quando há dados externos de alta qualidade."""
    status = InstanceStatus(url="https://test.example")
    
    # Com dados externos bons
    status.update_external_metrics(ExternalMetrics(
        uptime_day=100.0,
        tls_grade="A+",
        engine_count=30,
    ))
    score_with_external = status.calculate_tier_score()
    
    # Sem dados externos
    status._external_metrics = None
    score_without_external = status.calculate_tier_score()
    
    assert score_with_external > score_without_external


def test_tls_grades_affect_score():
    """TLS A+ deve ter score maior que TLS C."""
    status_a_plus = InstanceStatus(url="https://a.plus")
    status_a_plus.update_external_metrics(ExternalMetrics(tls_grade="A+", engine_count=20))
    
    status_c = InstanceStatus(url="https://c.grade")
    status_c.update_external_metrics(ExternalMetrics(tls_grade="C", engine_count=20))
    
    assert status_a_plus.calculate_tier_score() > status_c.calculate_tier_score()


def test_recency_decay():
    """Score de recência decai ao longo do tempo."""
    import time
    
    status = InstanceStatus(url="https://test.example")
    status.last_success = time.time()  # Agora
    immediate_recency = status._calculate_recency_bonus()
    
    status.last_success = time.time() - 7200  # 2 horas atrás
    old_recency = status._calculate_recency_bonus()
    
    assert immediate_recency > old_recency
```

---

## Referências

- [Circuit Breaker Pattern](docs/developer/arquitetura.md)
- [API searx.space](https://searx.space/data/instances.json) - Documentação informal via código existente
- [Issue #5](https://github.com/hemeligur/searxng-instance-mcp/issues/5)

---

## Status History

| Data | Status | Notas |
|------|--------|-------|
| 2025-10-07 | Proposto | RFC criado com score puramente inferido |
| 2025-01-19 | Draft | Melhorado para score híbrido (externo + interno) |
