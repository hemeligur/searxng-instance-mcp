# Active Context

## Melhoria da Documentação (2025-10-06)

### Problema Identificado
README.md não deixava claro que o MCP é um **cliente** que usa instâncias públicas online, não um servidor de instâncias locais.

### Ações Realizadas
1. **Rewrote completo do README.md**
   - Nova seção "Como Funciona" com diagrama claro no topo
   - Nota de destaque sobre instâncias públicas vs locais
   - Seção "O que é?" reformulada
   - Diagrama de arquitetura melhorado

2. **Criado `docs/searxng-local.md`**
   - Documentação sobre como rodar instância local (Docker)
   - Comparação cliente MCP vs instância local
   - Referência cruzada no README

### Resultado
✅ Usuários agora entendem claramente:
- Este é um cliente que conecta a instâncias públicas
- Não é um servidor de instâncias
- Para local, há documentação específica

---

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

## Bugs Investigados (2025-10-07)

### Issue #3 - results_limit ignorado
- **URL**: https://github.com/hemeligur/searxng-instance-mcp/issues/3
- **Problema**: Parâmetro `results_limit` não funciona
- **Status**: Aberto - não prioritário (comportamento esperado da API SearXNG)

### Issue #4 - HTTP 429/503 tratado como sucesso ✅ CORRIGIDO
- **URL**: https://github.com/hemeligur/searxng-instance-mcp/issues/4
- **Problema**: Rate limiting retorna 0 resultados mas é marcado como sucesso
- **Causa**: SearXNG retorna HTTP 200 com JSON vazio ao invés de HTTP 429

#### Solução Implementada
1. **Detecção de rate limiting implícito** (`manager.py`):
   - Respostas HTTP 200 com `{"results": []}` agora são tratadas como `success=False`
   - Flag `rate_limited=True` adicionado ao `SearchResponse`

2. **Suporte a HTTP 418/403**:
   - Códigos 418 (anti-bot) e 403 (forbidden) tratados como rate limiting

3. **Propagação do flag**:
   - `rate_limited` propagado para resposta final agregada
   - Circuit breaker atualizado corretamente

4. **Testes adicionados** (6 novos):
   - `test_rate_limited_empty_results_marked_as_failure`
   - `test_rate_limited_empty_body_marked_as_failure`
   - `test_http_418_treated_as_failure`
   - `test_http_403_treated_as_failure`
   - `test_rate_limited_falls_back_to_next_instance`
   - `test_rate_limited_circuit_breaker_updated`

#### Arquivos Alterados
- `src/searxng_mcp/models.py`: Added `rate_limited` field to `SearchResponse`
- `src/searxng_mcp/manager.py`: Added empty results detection, HTTP 418/403 handling
- `tests/test_manager.py`: Added 6 new tests for rate limiting scenarios

---

## Configuração via Environment Variables (2025-10-07)

### CFG-001 Implementado
Implementação de configuração via environment variables para controle de instâncias e tools de debug.

#### Novas Variáveis de Ambiente
| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_DISABLED_INSTANCES` | (vazio) | URLs de instâncias a desabilitar permanentemente |
| `SEARXNG_DEBUG_TOOLS` | `false` | Habilita tools de debug (opt-in) |
| `SEARXNG_BACKOFF_BASE` | `60` | Backoff base em segundos |
| `SEARXNG_BACKOFF_MAX` | `900` | Backoff máximo em segundos |

#### Arquitetura de Implementação
1. **`constants.py`**: Helpers para ler env vars com valores padrão
2. **`models.py`**: Campo `disabled` no `InstanceStatus`
3. **`server.py`**: Registro condicional de debug tools (só se `SEARXNG_DEBUG_TOOLS=true`)
4. **`manager.py`**: Aplica lista de desabilitados na inicialização
5. **`persistence.py`**: Filtra instâncias desabilitadas ao salvar/carregar

#### Casos de Uso
```bash
# Desabilitar instâncias com problemas (anti-bot)
SEARXNG_DISABLED_INSTANCES="https://search.ctq.ro" uv run python -m searxng_mcp

# Habilitar debug tools
SEARXNG_DEBUG_TOOLS=true uv run python -m searxng_mcp

# Via mcp.json
{
  "env": {
    "SEARXNG_DISABLED_INSTANCES": "https://search.ctq.ro,https://bad.com",
    "SEARXNG_DEBUG_TOOLS": "false"
  }
}
```

#### Testes
19 novos testes em `tests/test_config.py` cobrindo:
- Parsing de `SEARXNG_DISABLED_INSTANCES`
- Valores truthy para `SEARXNG_DEBUG_TOOLS`
- Configuração de backoff via env vars
- Comportamento do campo `disabled`

---

## RFC-001 - Sistema de Tiering por Qualidade (2025-10-07)

### Proposta
Implementar sistema de pontuação para classificar instâncias em **3 tiers**:

| Tier | Score | Nome | Estratégia |
|------|-------|------|------------|
| T1 | ≥ 0.75 | Premium | Prioridade máxima |
| T2 | 0.40-0.74 | Standard | Fallback |
| T3 | < 0.40 | Risky | Último recurso |

### Fórmula do Score
```
score = (success_rate × 0.4) + (recency_bonus × 0.3) + 
        (circuit_score × 0.2) + (failure_penalty × 0.1)
```

### Localização
- `docs/rfc/001-instance-quality-tiers.md`

### Status
📋 **Documentado** - Aguardando implementação futura

---

## CFG-002 - Discovery Dinâmico Corrigido (2025-10-07)

### Problema
A API do searx.space estava retornando **404** no endpoint `/api/v1/instances`. O sistema estava usando apenas **3-4 instâncias fallback**.

### Investigação Realizada
1. **Testei múltiplos endpoints**:
   - `https://searx.space/api/v1/instances` → **404** ❌
   - `https://searx.space/data/instances.json` → **200** ✅ (endpoint correto!)
   - `https://github.com/purujawa06-bot/SearXNG-active-instance` → **200** ✅

2. **Estrutura da API corrigida**:
   - URL é agora a **chave** do dicionário, não um campo `url`
   - `uptime` está no nível raiz, não em `network.uptime`
   - Engines é um **dict** com nomes como chaves

### Soluções Implementadas

#### 1. Novo Endpoint da API (`discovery.py`)
```python
SEARX_SPACE_API = "https://searx.space/data/instances.json"  # Era /api/v1/instances
```

#### 2. Fallback para GitHub Active Instances (`discovery.py`)
```python
GITHUB_ACTIVE_INSTANCES_URL = (
    "https://raw.githubusercontent.com/purujawa06-bot/SearXNG-active-instance/main/active.json"
)
```
- Provedor externo que verifica instâncias com JSON search funcionando
- Retorna apenas instâncias que passaram no teste: HTTP 200 + JSON válido

#### 3. Lista Expandida de Fallbacks
```python
FALLBACK_INSTANCES = [
    # Primary reliable instances
    "https://sx.xo.st",
    "https://search.ctq.ro",
    "https://www.isci.si",
    # Additional from searx.space (TLS A+, 100% uptime)
    "https://searx.ononoki.org",
    "https://search.femboy.ad",
    "https://searx.tiekoetter.com",
    "https://baresearch.org",
    "https://search.yuri.llc",
    "https://search.lumy.live",
    # From similar MCP projects
    "https://metacat.online",
    "https://search.080609.xyz",
    "https://search.canine.tools",
    "https://search.indst.eu",
]  # Total: 13 instâncias
```

#### 4. Estratégia de Fallback em Cascata
```
1. Cache válido → retorna cache
2. searx.space/data/instances.json → até 20 instâncias filtradas
3. GitHub active instances → instâncias verificadas JSON
4. Fallback hardcoded → 13 instâncias sempre disponíveis
```

### Resultados
- **Antes**: ~3 instâncias usadas
- **Depois**: **20 instâncias** do searx.space API + 13 fallbacks
- **Testes**: 60 passando ✅

### Arquivos Alterados
| Arquivo | Mudança |
|---------|---------|
| `discovery.py` | Endpoint corrigido, GitHub fallback, lista expandida |
| `models.py` | `from_api_response()` atualizado para novo formato |
| `tests/test_discovery.py` | Novos testes para GitHub fallback |
| `tests/conftest.py` | Fixture atualizada para novo formato |

---

## Melhorias de Resiliência (2025-10-07)

### Problema Identificado
- Estado não persistia entre execuções do servidor MCP
- Backoff inexistente - instâncias rate limited eram chamadas repetidamente
- Apenas 3 fallback instances usadas, sem distribuição de carga
- Discovery não funcionava em contexto async

### Soluções Implementadas

#### 1. Singleton Pattern (`manager.py`)
- `SearXNGManager` agora é singleton global
- `async_get_manager()` garante instância única
- Estado mantido em memória durante vida do servidor

#### 2. Persistência de Estado (`persistence.py` - NOVO)
```
~/.cache/searxng-mcp/instance_state.json
```
- Salva/carrega estado de circuit breaker e backoff
- Preserva estado entre reinicializações do servidor

#### 3. Backoff Exponencial (`models.py`)
```python
# Backoff exponencial por falha
1 falha  → 60s
2 falhas → 120s
3 falhas → 240s
4 falhas → 480s
5+ falhas → 900s (max)
```

#### 4. Circuit Breaker Aprimorado
- Estado: CLOSED → OPEN → HALF_OPEN
- 3 falhas consecutivas = OPEN
- 5 minutos TTL para transição OPEN → HALF_OPEN

#### 5. Distribuição de Carga
- Instâncias embaralhadas (shuffle) a cada inicialização
- Fallback automático para próxima instância disponível

### Novas Tools MCP
1. **`get_instances_status`** - Status completo de todas instâncias
2. **`reset_instance(url)`** - Resetar backoff de instância específica
3. **`get_available_instances`** - Lista instâncias disponíveis

### Arquivos Alterados/Criados
| Arquivo | Mudança |
|---------|---------|
| `models.py` | +Exponential backoff, `backoff_until`, `to_dict()` |
| `persistence.py` | **NOVO** - Load/save estado em disco |
| `manager.py` | +Singleton, +shuffle, +persistência |
| `server.py` | +3 novas tools |
| `__init__.py` | Versão 0.2.0 |
| `tests/test_manager.py` | Rewritten, +7 novos testes |

### Testes
```
57 testes passando
```

---

## Status Atual
✅ **PRODUTO PRONTO** - MCP funcionando globalmente no Pi
✅ **Issue #4 CORRIGIDO** - Rate limiting detectado + backoff exponencial + persistência
✅ **CFG-001 IMPLEMENTADO** - Configuração via env vars (disabled instances + debug tools)
✅ **CFG-002 IMPLEMENTADO** - Discovery dinâmico corrigido (API searx.space + GitHub fallback)
⚠️ **Issue #3 ABERTO** - results_limit não funciona (comportamento esperado da API)

## Estrutura do Projeto (v0.2.0)

```
searxng-mcp/
├── src/searxng_mcp/
│   ├── __init__.py       # v0.2.0
│   ├── __main__.py       # Entry point
│   ├── constants.py      # FALLBACK_INSTANCES, configs
│   ├── discovery.py      # InstanceDiscovery (searx.space API)
│   ├── manager.py        # SearXNGManager (singleton + persistência)
│   ├── models.py         # CircuitState, SearchResult, backoff
│   ├── persistence.py    # Estado em disco (~/.cache/)
│   └── server.py         # FastMCP + 4 tools
├── tests/                # 57 testes (pytest)
├── memory-bank/          # Documentação
├── pyproject.toml
└── README.md
```

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
├── tests/                # 57 testes (pytest)
├── memory-bank/          # Documentação
├── pyproject.toml
├── README.md
└── .pi/mcp.json         # REMOVIDO (usa registro global)
```
