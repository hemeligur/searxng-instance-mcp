# Active Context

## Tarefa Atual
📋 **Planejamento** - Documentar arquitetura e criar tarefas

## Decisões Recentes

| Data | Decisão | Justificativa |
|------|---------|---------------|
| 2025-10-05 | Discovery dinâmico de instâncias | Evitar hardcoding, usar searx.space API |
| 2025-10-05 | Python com uv | Stack moderna, gerenciamento fácil |
| 2025-10-05 | Cache local em ~/.cache/ | Reduzir chamadas à API, melhorar performance |
| 2025-10-05 | Circuit breaker com TTL 5min | Evitar usar instâncias problemáticas |

## Perguntas em Aberto

1. **Devo implementar health check periódico?**
   - Consideração: Pode adicionar latência na inicialização
   - Alternativa: Lazy health check (só testa quando vai usar)

2. **Quantas instâncias máximo no pool?**
   - Consideração: Muitas = mais opções, mas mais tempo de fallback
   - Sugestão: Limitar a 10-20 melhores por uptime

3. **Como tratar instâncias que retornam resultados diferentes?**
   - Consideração: Meta-busca pode ter inconsistências
   - Decisão: Não normalizar, retornar como vier do SearXNG

## Próximos Passos Imediatos

1. Criar `pyproject.toml`
2. Criar estrutura de diretórios `src/searxng_mcp/`
3. Implementar `discovery.py`
4. Implementar `manager.py`
5. Implementar `server.py`
