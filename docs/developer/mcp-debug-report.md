# MCP Server Debug Report - SearXNG Instance MCP

**Data:** 2025-10-06  
**Projeto:** searxng-instance-mcp  
**Status:** 🟡 Parcialmente Funcional

---

## Resumo Executivo

O servidor MCP SearXNG está **conectado e listando a ferramenta `web_search` corretamente**, porém quando tentamos executar a ferramenta através do Pi, ocorre um erro de validação de parâmetros antes que a requisição seja enviada ao servidor.

### Sintoma
```
mcp__searxng_web_search__web_search({query: "python"})
→ "Invalid request parameters"
```

### Testes Funcionam
- Execução direta do manager: ✅
- Execução via `uv run python -m searxng_mcp`: ✅
- `pi mcp list` mostra a ferramenta: ✅
- Qualquer tentativa de chamar a ferramenta: ❌

---

## Diagnóstico

### 1. Teste de Conectividade

```bash
$ pi mcp list
searxng-web-search: connected, 1 tool (codemode, project)
  uv run python -m searxng_mcp
  tools: web_search
```

**Resultado:** ✅ O servidor conecta e lista a ferramenta corretamente.

### 2. Teste de Funcionalidade Direta

```python
from searxng_mcp.manager import SearXNGManager
import asyncio

manager = SearXNGManager()
result = await manager.search("python", limit=3)
print(result.to_dict())
```

**Resultado:** ✅ Retorna 28+ resultados do sx.xo.st

### 3. Teste via MCP (Pi Agent)

```javascript
mcp__searxng_web_search__web_search({query: "python"})
```

**Resultado:** ❌ `Invalid request parameters`

---

## Tentativas de Solução

### Tentativa 1: Schema Minimalista
**Data:** 2025-10-06 00:47

Removemos todas as propriedades opcionais do schema:

```python
inputSchema={
    "type": "object",
    "properties": {
        "query": {"type": "string"},
    },
    "required": ["query"],
}
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 2: Schema com Títulos
**Data:** 2025-10-06 00:48

Adicionamos títulos às propriedades:

```python
inputSchema={
    "type": "object",
    "properties": {
        "query": {"type": "string", "title": "Query"},
    },
    "required": ["query"],
}
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 3: Schema com $schema
**Data:** 2025-10-06 00:49

Adicionamos referência ao JSON Schema:

```python
inputSchema={
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {"type": "string"},
    },
    "required": ["query"],
}
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 4: Sem Propriedades Opcionais
**Data:** 2025-10-06 00:51

Removemos `results_limit` completamente do schema:

```python
inputSchema={
    "type": "object",
    "properties": {
        "query": {"type": "string"},
    },
    "required": ["query"],
}
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 5: Mudança de Exposição
**Data:** 2025-10-06 00:52

Testamos com diferentes configurações de `exposure`:

```json
{
  "exposure": "direct"
}
```

**Resultado:** ❌ Mesmo erro (apenas muda como a ferramenta é exposta ao modelo)

---

### Tentativa 6: Registro Global vs Local
**Data:** 2025-10-06 00:55

Testamos registrar o servidor globalmente:

```bash
pi mcp add searxng-global -- uv run python -m searxng_mcp
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 7: Simplificação Total do Handler
**Data:** 2025-10-06 00:58

Simplificamos o handler ao máximo:

```python
async def call_tool_handler(ctx, params):
    return CallToolResult(content=[TextContent(type="text", text="OK")])
```

**Resultado:** ❌ Mesmo erro

---

### Tentativa 8: Verificação de Tipos do MCP SDK
**Data:** 2025-10-06 00:59

Verificamos a versão do MCP:

```
mcp==2.3.0
```

Verificamos o tipo `CallToolResult`:

```python
CallToolResult(
    content=[TextContent(...)],
    is_error=False  # Era isError antes, corrigimos
)
```

**Resultado:** ⚠️ `is_error` vs `isError` era um problema menor

---

## Hipóteses

### 1. Validação de Parâmetros do Pi (Mais Provável)
O Pi pode estar validando os parâmetros **antes** de enviar ao servidor MCP, usando uma implementação diferente de validação JSON Schema.

**Evidência:**
- O servidor conecta e lista ferramentas
- O erro ocorre imediatamente ao tentar chamar
- Não há logs no servidor quando o erro ocorre

### 2. Bug no MCP SDK Python
A versão 2.3.0 do MCP SDK pode ter um bug na forma como o schema é serializado.

### 3. Bug no Pi Agent
Pode haver um bug específico na validação de ferramentas MCP customizadas.

---

## Logs Coletados

### Log do Servidor (inicia corretamente)
```
2026-10-05 00:45:32,576 - searxng_mcp.server - INFO - Starting searxng-web-search v0.1.0 MCP server...
```

### Log do Pi (não há log visível)
```
~/.pi/agent/mcp.log não existe
```

### Processo do Servidor (em execução)
```
guilher+ 1151414  searxng_mcp  uv run python -m searxng_mcp
guilher+ 1151417  python3      -m searxng_mcp
```

---

## Soluções Alternativas Testadas

### WebScout (Funciona)
O MCP webscout integrado funciona corretamente:

```javascript
mcp__webscout__DuckDuckGoWebSearch({query: "python programming"})
→ ✅ Retorna resultados
```

### Execução Direta (Funciona)
O código pode ser executado diretamente sem problemas.

---

## Recomendações

### Imediatas
1. **Usar WebScout** como alternativa temporária
2. **Reportar bug** no repositório do Pi ou MCP SDK
3. **Testar com outro cliente MCP** (Claude Desktop, Cursor, etc.)

### Investigação Futura
1. Verificar se o problema persiste em outros clientes MCP
2. Testar com versões diferentes do MCP SDK
3. Examinar o código-fonte do Pi para entender a validação
4. Criar um caso de teste mínimo reprodutível

---

## Comandos Úteis

```bash
# Verificar status dos servidores MCP
pi mcp list

# Adicionar servidor
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp

# Remover servidor
pi mcp remove -l searxng-web-search

# Reiniciar servidor (força reload)
pi mcp remove -l searxng-web-search && sleep 1 && pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp

# Testar servidor diretamente
uv run python -c "from searxng_mcp.manager import SearXNGManager; import asyncio; print(asyncio.run(SearXNGManager().search('python', 3)))"
```

---

## Estrutura do Projeto

```
searxng-instance-mcp/
├── src/searxng_mcp/
│   ├── __init__.py
│   ├── __main__.py          # Entry point para python -m
│   ├── constants.py          # Configurações
│   ├── discovery.py          # Instance discovery
│   ├── manager.py            # Pool + circuit breaker
│   ├── models.py             # Data classes
│   └── server.py             # MCP server
├── tests/                    # 27 testes passando
├── .pi/mcp.json            # Config Pi
├── pyproject.toml
└── docs/
    └── mcp-debug-report.md   # Este documento
```

---

## Conclusão

O servidor MCP SearXNG está **técnicamente correto** e funcional quando testado fora do contexto do Pi. O problema parece estar na **camada de validação de parâmetros do Pi**, que rejeita as requisições antes de enviá-las ao servidor.

**Próximos passos recomendados:**
1. Testar com cliente MCP diferente
2. Reportar como issue no Pi ou MCP SDK
3. Aguardar correções ou buscar workarounds
