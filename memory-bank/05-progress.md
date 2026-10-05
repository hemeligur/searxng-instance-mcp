# Progress

## Status Geral
🟢 **Em Implementação** - Core concluído, faltando testes

## Marcos

- [x] Memory Bank inicializado
- [x] Plano de tarefas documentado
- [x] Estrutura base do projeto criada (pyproject.toml, diretórios)
- [x] Implementação do discovery dinâmico
- [x] Implementação do SearXNGManager
- [x] Implementação do servidor MCP
- [x] Configuração do Pi (.pi/mcp.json)
- [x] Documentação README.md
- [ ] Testes básicos

## Histórico de Mudanças

### 2025-10-06
- **T-030, T-031**: Implementado servidor MCP em `server.py`
  - Ferramenta `web_search(query, results_limit)` exposta via SDK MCP
  - Handler `call_tool()` processa buscas e retorna JSON
  - Função `main()` inicia servidor stdio com initialization options
  - Validação de inputs e tratamento de erros robusto
  - Logging configurado para debugging

- **T-020**: Implementado `SearXNGManager` em `manager.py`
  - Circuit breaker com estados CLOSED → OPEN → HALF_OPEN
  - TTL de 5 minutos para transição OPEN → HALF_OPEN
  - Método `search()` com fallback automático entre instâncias
  - `_try_instance()` para requisições assíncronas
  - `get_status_summary()` para debugging
  - `reset_circuit()` para reset manual

### 2025-10-05 (continuação)
- **T-010**: Implementado `discovery.py`
  - `discover_instances()` - busca e filtra instâncias do searx.space API
  - Cache em `~/.cache/searxng-mcp/instances.json` com TTL configurável
  - Fallback para instâncias hardcoded quando API indisponível
  - Type hints completos

### 2025-10-05
- Memory bank inicializado
- Plano documentado em 07-tasks.md
- **T-001 a T-004**: Estrutura base implementada
  - `pyproject.toml` com dependências (mcp, httpx, tenacity)
  - `src/searxng_mcp/` com `__init__.py`, `models.py`, `server.py`
  - README.md criado
  - Dependências instaladas via `uv sync`
- Repositório GitHub criado (privado)
