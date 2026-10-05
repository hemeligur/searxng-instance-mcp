# System Patterns

## Padrões Arquiteturais

### 1. Discovery Pattern
```
┌─────────────────────────────────────────────┐
│  InstanceDiscovery                         │
├─────────────────────────────────────────────┤
│  - Busca instâncias de searx.space API     │
│  - Filtra por: uptime >95%, TLS A+, etc.   │
│  - Cache local com TTL de 1 hora            │
│  - Fallback para lista hardcoded           │
└─────────────────────────────────────────────┘
```

### 2. Circuit Breaker Pattern
```
┌─────────────────────────────────────────────┐
│  Estado da Instância                       │
├─────────────────────────────────────────────┤
│  CLOSED ──(falha)──▶ OPEN                  │
│    ▲                    │                   │
│    │                    │ (TTL: 5 min)      │
│    │                    ▼                   │
│    └──────(sucesso)──▶ HALF_OPEN           │
└─────────────────────────────────────────────┘

Estados:
- CLOSED: Funcionando normalmente
- OPEN: Marcada como indisponível
- HALF_OPEN: Testando se voltou
```

### 3. Retry Pattern
```
Tentativa 1 ──(falha)──▶ Tentativa 2 ──(falha)──▶ Tentativa 3 ──(falha)──▶ Erro
     │                       │                       │
     ▼                       ▼                       ▼
  Instância A            Instância B            Instância C
```

## Fluxo de Busca

```
1. Cliente chama web_search(query, results_limit)
           │
           ▼
2. SearXNGManager.get_results()
           │
           ▼
3. Para cada instância no pool:
   a. Verificar circuit breaker (não está OPEN)
   b. Fazer requisição HTTP
   c. Se sucesso → retornar resultados
   d. Se falha (429, timeout, etc.) → próxima instância
           │
           ▼
4. Se todas falharem → retornar erro estruturado
```

## Códigos de Erro Tratados

| Código | Causa | Ação |
|--------|-------|------|
| 429 | Rate limit | Tentar próxima instância |
| 408 | Timeout | Tentar próxima instância |
| 5xx | Erro servidor | Tentar próxima instância |
| ConnectionError | Sem acesso | Tentar próxima instância |
| JSONDecodeError | Resposta inválida | Tentar próxima instância |

## Formato de Resposta

```json
{
  "success": true,
  "query": "python programming",
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "Experienced programmers in any other language...",
      "engine": "bing"
    }
  ],
  "instance_used": "sx.xo.st"
}
```

## Erro Estruturado

```json
{
  "success": false,
  "error": "all_instances_failed",
  "message": "Todas as instâncias SearXNG falharam",
  "details": [
    {"instance": "sx.xo.st", "error": "rate_limit"},
    {"instance": "xka.cz", "error": "timeout"}
  ]
}
```
