# Active Context

## Status Atual
✅ **PRODUTO PRONTO** - MCP funcionando globalmente no Pi

## Configuração Pi (2025-10-06)

### Registro Global
O servidor está registrado globalmente em `/home/guilherme/.pi/agent/mcp.json`:

```json
{
  "mcpServers": {
    "searxng-web-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/Arquivos_B/Documents/Guilherme/Projects/Dev/MCPs/searxng-instance-mcp",
        "run",
        "python",
        "-m",
        "searxng_mcp"
      ],
      "exposure": "direct"
    }
  }
}
```

### Uso
```javascript
mcp__searxng_web_search__web_search({query: "python", results_limit: 3})
// ✅ Retorna 10 resultados do SearXNG
```

## Histórico da Correção

### Bug Original
Erro `Invalid request parameters` ao chamar via Pi.

### Causa
API antiga do MCP SDK incompatível com protocolo moderno do Pi.

### Solução
- Migrou de `mcp[cli]>=1.0.0` para `fastmcp>=4.0.0`
- Reescreveu `server.py` usando `@mcp.tool()` decorator

### Commits
- `0822031` - fix: migrate from mcp SDK to FastMCP 4
- `14fb4dd` - docs: update memory bank with FastMCP fix
- `5716722` - Merge PR #1 (fix/fastmcp-migration → main)

## Repositório

**URL:** https://github.com/hemeligur/searxng-instance-mcp  
**Branch:** main  
**Último commit:** `5716722` - Merge pull request #1

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
│   └── server.py         # FastMCP server
├── tests/                # 27 testes
├── docs/                 # Debug report
├── .pi/mcp.json         # REMOVIDO (usa global)
├── pyproject.toml
├── README.md
└── memory-bank/
```
