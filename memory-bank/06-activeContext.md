# Active Context

## Tarefa Atual
📋 **Aguardando Testes** - Fase 7 do backlog

## Decisões Recentes

| Data | Decisão | Justificativa |
|------|---------|---------------|
| 2025-10-05 | Discovery dinâmico via searx.space API | Evitar hardcoding, usar instâncias verificadas |
| 2025-10-05 | Python com uv | Stack moderna, gerenciamento fácil |
| 2025-10-05 | Cache local em ~/.cache/ | Reduzir chamadas à API, melhorar performance |
| 2025-10-05 | Circuit breaker com TTL 5min | Evitar usar instâncias problemáticas |
| 2025-10-06 | API MCP via add_request_handler | Correção após erro de API |

## Validações Realizadas

| Teste | Resultado | Observação |
|-------|-----------|------------|
| Import all modules | ✅ OK | Todos os módulos importam corretamente |
| Server name | ✅ OK | `searxng-web-search` |
| Fallback instances | ✅ OK | 4 instâncias configuradas |
| MCP SDK | ✅ OK | Handlers registrados corretamente |
| Type hints | ⚠️ Pendente | pyright não executado |

## Próximos Passos Imediatos

1. **T-060**: Teste básico de conexão com instância SearXNG
2. **T-061**: Teste de fallback (simular falha de instância)
3. **T-062**: Teste de cache de instâncias

## Perguntas em Aberto

1. **Devo adicionar testes automatizados com pytest?**
   - Consideração: pytest já suportado, mas não instalado
   - Alternativa: pytest opcional em `dev` extras

2. **Quando o servidor iniciar, deve fazer discovery imediatamente?**
   - Consideração: Pode adicionar latência
   - Alternativa: Lazy discovery (só busca quando necessário)

## Conhecimento Adquirido

### API MCP SDK
- `Server.add_request_handler(method, RequestType, handler)` registra handlers
- `ListToolsResult` e `CallToolResult` são os tipos de retorno
- `TextContent(type="text", text=...)` para conteúdo de texto

### Padrões Implementados
- **Circuit Breaker**: CLOSED → OPEN → HALF_OPEN (3 falhas = OPEN, TTL 5min)
- **Fallback em Cascata**: tenta próxima instância se anterior falhar
- **Cache com TTL**: ~/.cache/searxng-mcp/instances.json (1 hora)

## Notas de Debug

### Erro Anterior - API MCP Incorreta
```python
# ❌ Errado - não existe on_list_tools()
@server.list_tools()
async def list_tools():
    ...

# ✅ Correto - usar add_request_handler
async def list_tools_handler(request):
    return ListToolsResult(tools=[...])

server.add_request_handler("tools/list", ListToolsRequest, list_tools_handler)
```

### Para Testar Manualmente
```bash
# Listar instâncias
uv run python -c "from searxng_mcp.discovery import discover_instances; import asyncio; print(asyncio.run(discover_instances()))"

# Testar busca
uv run python -c "from searxng_mcp.manager import SearXNGManager; import asyncio; m = SearXNGManager(); print(asyncio.run(m.search('python', 5)))"
```
