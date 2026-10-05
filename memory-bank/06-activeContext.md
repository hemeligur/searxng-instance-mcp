# Active Context

## Auditoria do Memory Bank

- **Data**: 2025-10-06
- **Harness**: Pi
- **Ações realizadas**:
  - Criado `08-completedTasks.md` com 13 tarefas concluídas
  - `07-tasks.md` limpo (todas pendentes movidas)
  - Versões de dependências corrigidas em `05-progress.md`
  - Estrutura do projeto atualizada em `04-techContext.md`

---

## Documentação (2025-10-06 - Atualizada)

### Documentação Criada
- `docs/developer/arquitetura.md` - Visão técnica da arquitetura com diagramas
- `docs/usuario/troubleshooting.md` - Guia de troubleshooting completo

### Documentação Atualizada
- `README.md` - Reestruturado como porta de entrada com links para docs/

### Estrutura de Documentação (reorganizada em 2025-10-06)
```
docs/
├── usuario/                 # Documentação para usuários
│   ├── searxng-guide.md    # Guia SearXNG (movido da raiz)
│   └── troubleshooting.md   # Troubleshooting
├── developer/               # Documentação para desenvolvedores
│   ├── arquitetura.md      # Arquitetura técnica
│   └── mcp-debug-report.md # Debug history
└── skill/                   # Skills do Pi
    └── searxng-skill.md   # Skill (movido da raiz)
```

---

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

Correção importante documentada em `08-completedTasks.md`.

### Resumo
- **Bug**: `Invalid request parameters` ao chamar via Pi
- **Solução**: Migrou de `mcp[cli]>=1.0.0` para `fastmcp>=4.0.0`
- **Commits**: `0822031`, `5716722` (PR #1)

## Repositório

**URL:** https://github.com/hemeligur/searxng-instance-mcp  
**Branch:** main  
**Último commit:** `5716722` - Merge pull request #1

## Estrutura do Projeto

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py       # exports main
│   ├── __main__.py       # Entry point (uv run python -m searxng_mcp)
│   ├── constants.py      # FALLBACK_INSTANCES, configs
│   ├── discovery.py      # InstanceDiscovery
│   ├── manager.py        # SearXNGManager
│   ├── models.py         # CircuitState, SearchResult
│   └── server.py         # FastMCP server
├── tests/                # 27 testes (pytest)
├── memory-bank/          # Documentação
├── pyproject.toml
├── README.md
└── .pi/mcp.json         # REMOVIDO (usa registro global)
```
