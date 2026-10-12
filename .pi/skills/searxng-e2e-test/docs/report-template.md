# E2E Test Report - SearXNG MCP

## 📋 Metadata

| Campo | Valor |
|-------|-------|
| **Data** | `YYYY-MM-DD HH:MM:SS` |
| **Duração Total** | `Xs` |
| **Ambiente** | `searxng-instance-mcp` |
| **Harness** | `Pi` |

---

## 📊 Resumo Executivo

| Métrica | Valor | Status |
|---------|-------|--------|
| Total de Testes | N | - |
| ✅ Aprovados | N | - |
| ❌ Falhas | N | - |
| Taxa de Sucesso | XX% | 🟢/🟡/🔴 |
| Instâncias Testadas | N | - |
| Busca Mais Rápida | Xms | 🟢/🟡/🔴 |
| Busca Mais Lenta | Xms | 🟢/🟡/🔴 |
| Tempo Médio | Xms | - |

### Status Indicators
- 🟢 Verde: Dentro do esperado (< 500ms, > 80% sucesso)
- 🟡 Amarelo: Atenção necessária (500-2000ms, 60-80% sucesso)
- 🔴 Vermelho: Problema crítico (> 2000ms, < 60% sucesso)

---

## 🔍 Resultados Detalhados

### T1: Busca Básica

| Status | Query | Resultados | Tempo | Instância |
|--------|-------|------------|-------|-----------|
| ✅/❌ | "python programming" | N | Xms | url |
| ✅/❌ | "site:github.com rust" | N | Xms | url |
| ✅/❌ | "what is machine learning" | N | Xms | url |

**Veredito T1**: `APROVADO` / `FALHOU`

---

### T2: Limite de Resultados

| Status | Limite Solicitado | Resultados Retornados | Tempo |
|--------|-------------------|----------------------|-------|
| ✅/❌ | 5 | N | Xms |
| ✅/❌ | 10 | N | Xms |
| ✅/❌ | 20 | N | Xms |

**Veredito T2**: `APROVADO` / `FALHOU`

---

### T3: Edge Cases

| Query | Tipo | Status | Resultado |
|-------|------|--------|-----------|
| `""` | vazia | ✅/❌ | error/message |
| `"a"` | curta | ✅/❌ | results/error |
| `"test & special <>"` | especiais | ✅/❌ | results/error |

**Veredito T3**: `APROVADO` / `FALHOU`

---

### T4: Circuit Breaker

| Métrica | Valor |
|---------|-------|
| Estado Inicial | closed/open/half_open |
| Reset Funcional | ✅/❌ |
| Transições Registradas | N |
| Circuit Breaker Working | ✅/❌ |

**Veredito T4**: `APROVADO` / `FALHOU`

---

### T5: Distribuição de Instâncias

| Instância | Utilizações | % do Total |
|-----------|-------------|------------|
| https://sx.xo.st | N | XX% |
| https://search.ctq.ro | N | XX% |
| https://xka.cz | N | XX% |

**Veredito T5**: `APROVADO` / `FALHOU`

---

## 📈 Métricas Adicionais

### Response Time Distribution
```
0-500ms:    [██████████] XX%
500-1000ms: [██████]     XX%
1000-2000ms:[██]         XX%
>2000ms:    [█]          XX%
```

### Instance Health (via get_instances_status)
| Instância | Estado | Falhas | Backoff Restante |
|-----------|--------|--------|------------------|
| url1 | closed | 0 | - |
| url2 | open | 3 | 60s |
| url3 | half_open | 1 | - |

---

## ⚠️ Problemas Encontrados

### Críticos
1. _(nenhum ou listar)_

### Warnings
1. _(nenhum ou listar)_

### Info
1. _(nenhum ou listar)_

---

## 💡 Recomendações

1. **Imediato**:
   - _(ações necessárias)_

2. **Curto Prazo**:
   - _(ações recomendadas)_

3. **Longo Prazo**:
   - _(melhorias estruturais)_

---

## 📝 Notas

_(espaço para observações adicionais)_

---

*Relatório gerado em: `YYYY-MM-DD HH:MM:SS`*
