---
name: searxng-e2e-test
description: Realiza testes end-to-end do web_search do searxng-instance-mcp usando as ferramentas MCP disponíveis. Use ao testar buscas, validar instâncias, verificar circuit breaker, ou gerar relatórios de qualidade do serviço.
---

# SearXNG E2E Test

Realiza testes end-to-end completos do MCP searxng-instance-mcp, validando todas as funcionalidades e gerando relatórios estruturados.

## Fluxo de Testes

### 1. Verificação Inicial do Estado

Antes de executar os testes, colete o estado atual das instâncias:

```javascript
// Verificar status geral das instâncias
const statusRaw = await tools.mcp__searxng_web_search__get_instances_status();
const status = JSON.parse(statusRaw.result);

// Verificar instâncias disponíveis
const availableRaw = await tools.mcp__searxng_web_search__get_available_instances();
const available = JSON.parse(availableRaw.result);
```

### 2. Suite de Testes

Execute os testes na ordem abaixo:

#### Test T1: Busca Básica
- **Objetivo**: Validar que `web_search` retorna resultados válidos
- **Queries de teste**:
  - `"python programming"` (termo genérico)
  - `"site:github.com rust programming"` (com modificador)
  - `"what is machine learning"` (pergunta)
- **Validações**:
  - `success: true`
  - `results.length > 0`
  - `instance_used` presente
  - Cada result com `url`, `title`, `content`

#### Test T2: Limite de Resultados
- **Objetivo**: Validar que `results_limit` funciona corretamente
- **Queries**: `web_search("python", results_limit=5)` e `web_search("python", results_limit=20)`
- **Validações**:
  - `count <= results_limit`
  - `results.length <= results_limit`

#### Test T3: Edge Cases
- **Objetivo**: Validar tratamento de casos especiais
- **Queries**:
  - Query vazia `""`
  - Query muito curta `"a"`
  - Query com caracteres especiais `"test & <query> with 'quotes'"`
- **Validações**:
  - Response estruturado (mesmo em erro)
  - `success: false` com `error` e `message`

#### Test T4: Circuit Breaker e Resiliência
- **Objetivo**: Validar que instâncias com falha são corretamente identificadas
- **Procedimento**:
  1. Fazer busca normal (inicializar circuit breaker)
  2. Forçar reset: `reset_instance("")` para resetar todas
  3. Verificar que `get_instances_status` atualiza corretamente
- **Validações**:
  - `state` transita entre `closed`, `open`, `half_open`
  - `failure_count` incrementa em falhas

#### Test T5: Distribuição por Instância
- **Objetivo**: Verificar que instâncias diferentes são usadas (distribuição de carga)
- **Procedimento**: Fazer 10 buscas idênticas e analisar `instance_used`
- **Validações**:
  - Múltiplas instâncias utilizadas (se disponíveis)
  - `instance_used` corresponde a instância real

### 3. Coleta de Métricas

Durante os testes, colete:

```javascript
const metrics = {
  tests: [],
  instanceUsage: {},
  responseTimes: [],
  errors: []
};
```

Para cada teste:
```javascript
const startTime = Date.now();
const result = JSON.parse(await tools.mcp__searxng_web_search__web_search({query: "...", results_limit: 10}));
const duration = Date.now() - startTime;

metrics.tests.push({
  name: "T1-basic",
  success: result.success,
  duration,
  resultsCount: result.count || 0
});

if (result.instance_used) {
  metrics.instanceUsage[result.instance_used] = 
    (metrics.instanceUsage[result.instance_used] || 0) + 1;
}

if (!result.success) {
  metrics.errors.push({
    test: "T1-basic",
    error: result.error,
    details: result.details
  });
}
```

### 4. Geração do Relatório

Após todos os testes, gere o relatório no formato:

```markdown
# E2E Test Report - SearXNG MCP

## Metadata
- **Data**: YYYY-MM-DD HH:MM:SS
- **Duração Total**: Xs
- **Ambiente**: [descrever ambiente]

## Resumo Executivo
| Métrica | Valor |
|---------|-------|
| Total de Testes | N |
| Testes Aprovados | N |
| Taxa de Sucesso | XX% |
| Instâncias Testadas | N |
| Busca Mais Rápida | Xms |
| Busca Mais Lenta | Xms |

## Resultados Detalhados

### T1: Busca Básica ✅/❌
- **Status**: APROVADO / FALHOU
- **Instância Utilizada**: URL
- **Resultados Retornados**: N
- **Tempo de Resposta**: Xms

### T2: Limite de Resultados ✅/❌
- Limite 5: N resultados (esperado ≤5)
- Limite 20: N resultados (esperado ≤20)

### T3: Edge Cases ✅/❌
| Query | Resultado |
|-------|-----------|
| "" | {error} |
| "a" | {result} |
| "test & special" | {result} |

### T4: Circuit Breaker ✅/❌
- **Estado Inicial**: {state}
- **Pós-Reset**: {state}
- **Transições**: {count}

### T5: Distribuição ✅/❌
| Instância | Utilizações |
|-----------|-------------|
| url1 | N |
| url2 | N |

## Problemas Encontrados

[Listar problemas se houver]

## Recomendações

[Listar recomendações baseadas nos resultados]
```

## Checklist de Execução

- [ ] Resetar estado antes de testar: `reset_instance("")`
- [ ] Verificar instâncias disponíveis: `get_available_instances`
- [ ] Executar T1-T5 na ordem
- [ ] Coletar métricas durante execução
- [ ] Gerar relatório final
- [ ] Documentar problemas encontrados

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Nenhuma instância disponível | Verificar conexão de rede, resetar instâncias |
| Todas buscas falham | Verificar se API searx.space está acessível |
| Timeout constante | Ajustar `SEARXNG_GLOBAL_TIMEOUT` no ambiente |
| Rate limiting frequente | Reduzir número de requisições de teste |
