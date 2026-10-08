# EPD-001: Search Results Cache

**Status**: Draft  
**Author**: Hemeligur  
**Created**: 2025-01-XX  
**Type**: Feature Enhancement

---

## Resumo

Implementar cache de resultados de busca no cliente MCP para evitar desperdício de requisições à API do SearXNG quando o parâmetro `results_limit` é menor que o número de resultados retornados (~10).

---

## Motivação

### Problema Atual

A API do SearXNG não suporta o parâmetro `limit`. Quando o cliente solicita 3 resultados, a API retorna ~10 resultados, e os 7 excedentes são simplesmente descartados.

**Fluxo atual (desperdício)**:
```
Cliente pede: limit=3
     │
     ▼
API retorna: ~10 resultados
     │
     ▼
Cliente descarta: 7 resultados ❌
```

### Problema Identificado (Issue #3)

- `results_limit` parameter is ignored
- API always returns ~10 results
- Extra results are wasted

### Solução Proposta

Armazenar os resultados "extras" em cache para reutilização em queries futuras, evitando requisições redundantes.

---

## Proposta de Solução

### Arquitetura do Cache

```
┌─────────────────────────────────────────────────────────────┐
│  Query: "python tutorial"                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Check cache (key = hash da query normalizada)          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
          Hit (cache fresco)              Miss
              │                               │
              ▼                               ▼
    ┌─────────────────┐            ┌─────────────────────┐
    │ Retornar do     │            │ Fazer requisição    │
    │ cache + filtrar  │            │ à instância        │
    │ por limit       │            │ Guardar TODOS os   │
    └─────────────────┘            │ ~10 resultados     │
              │                    └─────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Resultados     │
                    │ filtrados por  │
                    │ results_limit  │
                    └─────────────────┘
```

### Estrutura de Dados

```python
# ~/.cache/searxng-mcp/results.json

{
  "version": 1,
  "timestamp": 1735689600,  # Unix timestamp
  "entries": {
    "<sha256_hash>": {
      "query": "python tutorial",
      "normalized_query": "pythontutorial",
      "results": [
        {
          "url": "https://...",
          "title": "...",
          "content": "...",
          "engine": "google",
          "category": "general"
        },
        // ... ~10 resultados completos
      ],
      "instance_url": "https://sx.xo.st",
      "fetched_at": 1735689600
    }
  },
  "access_order": ["hash1", "hash2", "hash3"]  # LRU tracking
}
```

### Parâmetros de Configuração

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `SEARXNG_RESULTS_CACHE_TTL` | 300 (5 min) | TTL do cache de resultados em segundos |
| `SEARXNG_RESULTS_CACHE_MAX_ENTRIES` | 100 | Máximo de queries em cache (LRU) |

### Normalização de Query

Para garantir cache hits, queries são normalizadas:

```python
def normalize_query(query: str) -> str:
    """Normalize query for consistent cache keys."""
    return (
        query
        .strip()                    # Remover espaços nas bordas
        .lower()                    # Minúsculas
        .removeprefix("how to ")    # Remover prefixos comuns
        .removeprefix("what is ")
        .removeprefix("best ")
        .replace("  ", " ")        # Espaços duplos
        .replace(" ", "")           # Remover todos os espaços (opcional)
    )
```

**Exemplo**:
- `"  Python Tutorial  "` → `"pythontutorial"`
- `"How to Python"` → `"pythontutorial"`

### Políticas de Evição

1. **TTL-based**: Entradas expiram após `SEARXNG_RESULTS_CACHE_TTL`
2. **LRU**: Quando `max_entries` atingido, remove Least Recently Used
3. **Manual**: Função `clear_results_cache()` exposta via tool de debug

---

## Implementação Proposta

### Novos Arquivos

```
src/searxng_mcp/
├── __init__.py           # Exports
├── server.py             # + clear_results_cache tool (debug)
├── manager.py            # + results_cache integration
├── cache.py              # [NOVO] Search results cache
├── discovery.py          # (sem mudanças)
├── constants.py          # + cache config
├── models.py             # + CacheEntry
└── persistence.py        # + results cache file I/O
```

### Modificações em `manager.py`

```python
async def search(self, query: str, limit: int = DEFAULT_LIMIT) -> SearchResponse:
    # 1. Check cache first
    cache_key = get_cache_key(query)
    cached_entry = results_cache.get(cache_key)
    
    if cached_entry:
        # Cache hit - filter and return
        results = cached_entry.results[:limit]
        return SearchResponse(
            success=True,
            query=query,
            results=results,
            count=len(results),
            cache_hit=True,  # New field
        )
    
    # 2. Cache miss - fetch from instance
    response = await self._fetch_from_instance(url, query)
    
    # 3. Store ALL results in cache (not just 'limit')
    results_cache.set(cache_key, response.results)
    
    # 4. Return filtered results
    return SearchResponse(
        success=True,
        query=query,
        results=response.results[:limit],
        count=limit,
    )
```

### API de Debug (opcional)

```python
@mcp.tool()
async def clear_results_cache() -> str:
    """Limpa o cache de resultados de busca."""
    results_cache.clear()
    return json.dumps({"success": True, "message": "Cache cleared"})
```

---

## Análise de Impacto

### Benefícios

| Benefício | Impacto |
|-----------|---------|
| Economia de bandwidth | ~70% menos requisições para queries populares |
| Menor rate limiting | Menos bloqueios por parte das instâncias |
| Respostas mais rápidas | Cache hit = ~1ms vs ~500ms |
| Experiência do usuário | Queries repetidas são instantâneas |

### Trade-offs

| Trade-off | Mitigação |
|-----------|-----------|
| Complexidade de código | Módulo isolado, testes unitários |
| Freshness dos dados | TTL curto (5 min) |
| Uso de disco | ~500KB para 100 queries |
| Hit rate inicial | Aquecimento com queries populares |

### Compatibilidade

- ✅ Backward compatible (cache é transparente)
- ✅ Não afeta API existente
- ✅ Adiciona campo opcional `cache_hit` na resposta

---

## Testes Propostos

### Unit Tests

```python
def test_cache_key_normalization():
    assert normalize("  Python  ") == normalize("python")
    assert normalize("how to python") == normalize("pythontutorial")

def test_cache_hit_returns_filtered_results():
    cache.set("test", [r1, r2, r3, r4, r5])
    result = cache.get("test", limit=2)
    assert len(result) == 2
    assert result == [r1, r2]

def test_lru_eviction():
    for i in range(150):  # max=100
        cache.set(f"query{i}", [result])
    assert cache.size() == 100
```

### Integration Tests

```python
async def test_cache_miss_then_hit():
    # First call - cache miss
    result1 = await manager.search("python", limit=3)
    assert result1.cache_hit is False
    
    # Second call - cache hit
    result2 = await manager.search("python", limit=5)
    assert result2.cache_hit is True
```

---

## Cronograma (Estimativa)

| Fase | Tempo | Descrição |
|------|-------|-----------|
| Implementação | 2-4h | Módulo cache + integração |
| Testes | 1-2h | Unit + integration tests |
| Documentação | 1h | README update, CHANGELOG |
| **Total** | 4-7h | |

---

## Alternativas Consideradas

### 1. Sem Cache (Solução Simples)
- ✅ Implementação trivial
- ❌ Desperdiça ~70% dos dados retornados
- ❌ Mais rate limiting

### 2. Cache no Redis/External
- ✅ Persistência entre sessões
- ❌ Dependência externa
- ❌ Overhead de configuração

### 3. Multiple Page Requests
- ✅ Resultados frescos
- ❌ Mais requisições = mais rate limiting
- ❌ Latência maior

**Decisão**: Implementar cache local (opção 1 + cache) para melhor custo-benefício.

---

## Referências

- Issue #3: `results_limit` parameter is ignored
- [SearXNG Search API](https://docs.searxng.org/dev/search_api.html)
- [Python functools LRU Cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2025-01-XX | Draft | Initial proposal |
