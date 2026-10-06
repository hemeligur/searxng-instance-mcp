# Product Context

## O que é SearXNG?

SearXNG é um motor de meta-busca **privado e gratuito** que agrega resultados de diversos buscadores (Google, Bing, DuckDuckGo, etc.) sem rastrear ou perfilar usuários.

Referências:
- https://searxng.org
- https://searx.space (indexador de instâncias)
- https://docs.searxng.org

## O que é Este MCP?

Este projeto é um **CLIENTE MCP** que se conecta a instâncias SearXNG **PÚBLICAS/ONLINE**. Não é um servidor de instâncias.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────────────┐
│   Cliente   │────▶│  SearXNG MCP     │────▶│  Instâncias Públicas Online │
│   (Pi/AI)   │◀────│  (este projeto)  │◀────│  • sx.xo.st                 │
└─────────────┘     └──────────────────┘     │  • searxng.org             │
                              │                │  • (descobertas via        │
                              ▼                │   searx.space)             │
                       ┌──────────────────┐    └─────────────────────────────┘
                       │  Cache Local     │
                       │  (~/.cache/)     │
                       └──────────────────┘
```

**Nota importante**: Se você precisa de máxima privacidade ou quer rodar sua própria instância, consulte [docs/searxng-local.md](docs/searxng-local.md).

## Por que um MCP para SearXNG?

### Problema
- Instâncias públicas do SearXNG podem ficar indisponíveis
- Rate limiting pode bloquear requisições
- Cliente não deveria gerenciar essas complexidades

### Solução
- Pool de instâncias verificadas (públicas online)
- Fallback automático em caso de falha
- Abstração completa da infraestrutura

## Arquitetura Proposta

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Cliente   │────▶│  SearXNG MCP     │────▶│  Instance       │
│   (agente) │◀────│  Server          │◀────│  Discovery      │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                        │
                           ▼                        ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │  SearXNGManager  │     │  searx.space    │
                    │  (pool + retry)  │     │  (API JSON)     │
                    └──────────────────┘     └─────────────────┘
```

## Instâncias Conhecidas

| URL | Status | Observações |
|-----|--------|-------------|
| `https://sx.xo.st` | ✅ Boa | Uptime 100%, rápida |
| `https://xka.cz` | ⚠️ Rate limit | Funciona, mas com limites |
| `https://searxng.org` | ✅ Oficial | Instância pública oficial |
| `https://www.isci.si` | ✅ Backup | Alternativa confiável |

## Decisões de Design

1. **Discovery Dinâmico**: Carregar instâncias de searx.space na inicialização
2. **Cache Local**: Salvar lista de instâncias em `~/.cache/searxng-mcp/instances.json`
3. **Circuit Breaker**: Marcar instâncias com falha temporariamente (TTL: 5 min)
4. **Fallback em Cascata**: Tentar próxima instância se anterior falhar
5. **API JSON**: Usar endpoint `/search?q=...&format=json` do SearXNG
