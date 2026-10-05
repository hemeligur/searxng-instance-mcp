# Troubleshooting - SearXNG Instance MCP

## Problemas Comuns e Soluções

### 1. "All instances unavailable"

**Sintoma:**
```json
{
  "success": false,
  "error": "All instances unavailable"
}
```

**Causas possíveis:**
- Sem conexão com a internet
- Todas as instâncias estão com rate limit
- Firewall bloqueando requisições
- API searx.space indisponível

**Soluções:**

1. **Verifique conexão com internet:**
```bash
curl -s https://sx.xo.st/search?q=test&format=json
```

2. **Aguarde e tente novamente:**
   - Rate limits são temporários (geralmente 5-15 minutos)

3. **Limpe o cache forçando nova descoberta:**
```bash
rm -rf ~/.cache/searxng-mcp/
```

4. **Use instâncias específicas via variáveis:**
```bash
SEARXNG_CACHE_TTL=0 uv run python -m searxng_mcp
```

---

### 2. Rate Limiting

**Sintoma:**
```json
{
  "error": "Rate limited (429)"
}
```

**Soluções:**

1. **Aguarde** - Rate limits expiram automaticamente em alguns minutos

2. **O sistema faz fallback automático** para outras instâncias

3. **Limpe o cache** para usar instâncias diferentes:
```bash
rm -rf ~/.cache/searxng-mcp/
```

---

### 3. Timeout em Todas as Instâncias

**Sintoma:**
```json
{
  "error": "Request timeout"
}
```

**Causas:**
- Instância sobrecarregada
- Problemas de rede
- Firewall

**Soluções:**

1. **Verifique conectividade:**
```bash
ping -c 3 sx.xo.st
```

2. **Limpe o cache** para tentar instâncias diferentes:
```bash
rm -rf ~/.cache/searxng-mcp/
```

3. **Aumente o timeout** (requer modificação de código):
```python
# Em constants.py
DEFAULT_TIMEOUT: int = 30  # segundos
```

---

### 4. MCP Server Não Conecta

**Sintoma:**
```
searxng-web-search: not connected
```

**Soluções:**

1. **Remova e adicione novamente:**
```bash
pi mcp remove searxng-web-search
pi mcp add -l searxng-web-search -- uv run python -m searxng_mcp
```

2. **Verifique se o projeto está no caminho correto:**
```bash
ls /mnt/Arquivos_B/Documents/Guilherme/Projects/Dev/MCPs/searxng-instance-mcp/src/searxng_mcp/
```

3. **Verifique dependências:**
```bash
cd /mnt/Arquivos_B/Documents/Guilherme/Projects/Dev/MCPs/searxng-instance-mcp
uv sync
uv run python -c "from searxng_mcp import main; print('OK')"
```

---

### 5. Query Retorna Resultados Vazios

**Sintoma:**
```json
{
  "success": true,
  "query": "xyz",
  "results": [],
  "count": 0
}
```

**Soluções:**

1. **Verifique a query** - termo muito específico pode não ter resultados

2. **Tente com termo mais genérico:**
```python
# Exemplo
query = "python"  # Funciona
query = "xyz123nonexistent999"  # Não funciona
```

3. **Limpe o cache** para garantir instâncias atualizadas:
```bash
rm -rf ~/.cache/searxng-mcp/
```

---

### 6. Cache Antigo

**Sintoma:**
- Usando instâncias que não existem mais
- Instâncias com status diferente

**Soluções:**

1. **Limpe manualmente:**
```bash
rm -rf ~/.cache/searxng-mcp/
```

2. **Aguarde expiração** (1 hora por padrão)

3. **Redefina TTL via variável:**
```bash
SEARXNG_CACHE_TTL=0 uv run python -m searxng_mcp
```

---

### 7. Erro de Importação

**Sintoma:**
```
ModuleNotFoundError: No module named 'searxng_mcp'
```

**Soluções:**

1. **Instale dependências:**
```bash
uv sync
```

2. **Verifique se está no diretório correto:**
```bash
cd /mnt/Arquivos_B/Documents/Guilherme/Projects/Dev/MCPs/searxng-instance-mcp
```

3. **Execute o projeto:**
```bash
uv run python -m searxng_mcp
```

---

## Comandos de Debug

### Ver Status do Cache
```bash
cat ~/.cache/searxng-mcp/instances.json | jq .
```

### Verificar Instâncias
```python
from searxng_mcp.discovery import discover_instances
import asyncio

instances = asyncio.run(discover_instances(use_cache=False))
print(instances)
```

### Testar Manager
```python
from searxng_mcp.manager import SearXNGManager
import asyncio

manager = SearXNGManager()
result = asyncio.run(manager.search("python", limit=5))
print(result.to_dict())
```

### Ver Logs
```bash
# Execute com output de debug
uv run python -m searxng_mcp 2>&1 | grep -i "searxng"
```

---

## Debugging Avançado

### 1. Habilitar Logging Detalhado

Crie arquivo `debug_test.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from searxng_mcp.manager import SearXNGManager
import asyncio

async def main():
    manager = SearXNGManager()
    result = await manager.search("python", limit=3)
    print(result.to_dict())

asyncio.run(main())
```

Execute:
```bash
uv run python debug_test.py
```

### 2. Verificar Circuit Breaker

```python
from searxng_mcp.manager import SearXNGManager

manager = SearXNGManager()
summary = manager.get_status_summary()
print(summary)
```

### 3. Testar Instância Específica

```python
import httpx
import asyncio

async def test_instance():
    url = "https://sx.xo.st/search"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params={"q": "test", "format": "json"})
        print(response.json())

asyncio.run(test_instance())
```

---

## Contato e Suporte

- **Issue no GitHub:** https://github.com/hemeligur/searxng-instance-mcp/issues
- **Documentação SearXNG:** https://docs.searxng.org
- **Status SearXNG Instances:** https://searx.space
