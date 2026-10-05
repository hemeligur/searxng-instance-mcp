# Active Context

## Status Atual
📋 **Problema em Investigação** - MCP conecta mas chamada falha

## Problema: "Invalid request parameters"

O servidor MCP SearXNG conecta e lista a ferramenta `web_search` corretamente, mas quando o Pi tenta chamar a ferramenta, ocorre erro de validação **antes** de enviar a requisição ao servidor.

### Sintoma
```javascript
mcp__searxng_web_search__web_search({query: "python"})
// → "Invalid request parameters"
```

### Testes Realizados
| Teste | Resultado |
|-------|-----------|
| `pi mcp list` | ✅ mostra web_search |
| `uv run python -m searxng_mcp` | ✅ inicia servidor |
| Teste direto do manager | ✅ retorna resultados |
| Chamada via Pi | ❌ Invalid request parameters |

### Tentativas de Solução
1. ✅ Schema minimalista
2. ✅ Schema com títulos
3. ✅ Schema com $schema
4. ✅ Remover propriedades opcionais
5. ✅ Mudar exposure para direct
6. ✅ Registro global
7. ✅ Simplificar handler
8. ✅ Corrigir is_error vs isError

**Todas falharam com o mesmo erro.**

### Hipótese
Pi valida os parâmetros localmente antes de enviar ao servidor MCP.

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
