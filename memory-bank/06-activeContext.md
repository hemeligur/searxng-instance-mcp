# Active Context

## Status Atual
✅ **RESOLVIDO** - MCP funcionando corretamente via FastMCP 4

## Solução Implementada (2025-10-06)

### Problema Original
O servidor MCP usava API antiga de baixo nível (`mcp[cli]>=1.0.0` com `add_request_handler`), que não era compatível com o protocolo moderno do Pi.

### Correção
- **Dependência**: `mcp[cli]>=1.0.0` → `fastmcp>=4.0.0`
- **Código**: Reescrito `server.py` usando decorator `@mcp.tool()`
- **Entry point**: Corrigido `__main__.py`

### Resultado
```javascript
mcp__searxng_web_search__web_search({query: "python", results_limit: 3})
// ✅ Retorna 10 resultados do SearXNG
```

### Branch
`fix/fastmcp-migration` - commit `0822031`

## Decisões Recentes

| Data | Decisão | Justificativa |
|------|---------|---------------|
| 2025-10-06 | Criar docs/mcp-debug-report.md | Documentar problema para referência |
| 2025-10-06 | Manter servidor registrado | Facilita testes quando solução encontrada |
| 2025-10-06 | Corrigir is_error | MCP SDK usa is_error, não isError |

## Alternativa Temporária

Usar webscout que funciona:
```javascript
mcp__webscout__DuckDuckGoWebSearch({query: "python"})
// ✅ Funciona corretamente
```

## Notas de Debug

### API MCP - Handler Signatures
```python
# ✅ Correto - handlers recebem (ctx, params)
async def list_tools_handler(ctx, params) -> ListToolsResult:
    return ListToolsResult(tools=[...])

async def call_tool_handler(ctx, params) -> CallToolResult:
    name = params.name
    arguments = params.arguments or {}
    # ...

server.add_request_handler("tools/list", ListToolsRequest, list_tools_handler)
server.add_request_handler("tools/call", CallToolRequest, call_tool_handler)
```

### Para executar como módulo
```bash
uv run python -m searxng_mcp
```

### Registrar no Pi
```bash
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

### Testar diretamente
```bash
uv run python -c "
from searxng_mcp.manager import SearXNGManager
import asyncio
m = SearXNGManager()
print(asyncio.run(m.search('python', 3)))
"
```

## Próximos Passos

1. [ ] Testar com cliente MCP diferente (Claude Desktop, Cursor)
2. [ ] Reportar issue no Pi ou MCP SDK
3. [ ] Aguardar atualização do Pi/MCP SDK
4. [ ] Investigar código-fonte do Pi para validação

## Repositório

**URL:** https://github.com/hemeligur/searxng-instance-mcp  
**Branch:** main  
**Último commit:** `1d6d0f6` - fix: simplify tool schema and handler

## Estrutura do Projeto

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py       # exports main
│   ├── __main__.py       # Entry point
│   ├── constants.py      # FALLBACK_INSTANCES, configs
│   ├── discovery.py      # InstanceDiscovery
│   ├── manager.py        # SearXNGManager
│   ├── models.py         # CircuitState, SearchResult
│   └── server.py         # MCP server
├── tests/                 # 27 testes
├── docs/                  # Debug report
├── .pi/mcp.json         # Config Pi
├── pyproject.toml
├── README.md
└── memory-bank/          # Documentação
```
