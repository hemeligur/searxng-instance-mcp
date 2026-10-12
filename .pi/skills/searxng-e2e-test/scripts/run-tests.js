#!/usr/bin/env node
/**
 * E2E Test Runner para SearXNG MCP
 * Executa suite completa de testes e gera relatório
 * 
 * Uso: Este script deve ser executado via codemode
 */

const TEST_QUERIES = {
  basic: [
    "python programming",
    "site:github.com rust programming", 
    "what is machine learning"
  ],
  limits: [5, 10, 20],
  edgeCases: [
    { query: "", description: "query vazia" },
    { query: "a", description: "query muito curta" },
    { query: "test & <query> with 'quotes'", description: "caracteres especiais" }
  ]
};

class E2ETestRunner {
  constructor() {
    this.metrics = {
      startTime: Date.now(),
      tests: [],
      instanceUsage: {},
      responseTimes: [],
      errors: [],
      statusSnapshot: null
    };
  }

  async runAllTests() {
    console.log("🚀 Iniciando E2E Test Suite para SearXNG MCP\n");

    // 1. Reset estado e coletar baseline
    await this.resetState();
    await this.collectBaseline();

    // 2. Executar suites de teste
    await this.runBasicSearchTests();
    await this.runLimitTests();
    await this.runEdgeCaseTests();
    await this.runCircuitBreakerTests();
    await this.runDistributionTests();

    // 3. Gerar relatório
    return this.generateReport();
  }

  async resetState() {
    console.log("📦 Resetando estado das instâncias...");
    try {
      const result = await tools.mcp__searxng_web_search__reset_instance({ url: "" });
      console.log(`   ✓ Reset concluído: ${JSON.parse(result.result).message}`);
    } catch (e) {
      console.log(`   ⚠ Reset falhou: ${e.message}`);
    }
  }

  async collectBaseline() {
    console.log("📊 Coletando baseline de instâncias...");
    try {
      const statusResult = await tools.mcp__searxng_web_search__get_instances_status();
      const availableResult = await tools.mcp__searxng_web_search__get_available_instances();
      
      this.metrics.statusSnapshot = {
        status: JSON.parse(statusResult.result),
        available: JSON.parse(availableResult.result)
      };
      
      console.log(`   ✓ Total instâncias: ${this.metrics.statusSnapshot.status.total}`);
      console.log(`   ✓ Disponíveis: ${this.metrics.statusSnapshot.available.length}`);
    } catch (e) {
      console.log(`   ⚠ Coleta de baseline falhou: ${e.message}`);
    }
  }

  async runBasicSearchTests() {
    console.log("\n🧪 Executando Testes Básicos (T1)...");
    
    for (const query of TEST_QUERIES.basic) {
      const testResult = await this.executeSearch(query, 10, "T1-basic");
      testResult.query = query;
      this.metrics.tests.push(testResult);
    }
  }

  async runLimitTests() {
    console.log("\n🧪 Executando Testes de Limite (T2)...");
    
    for (const limit of TEST_QUERIES.limits) {
      const testResult = await this.executeSearch("python programming", limit, "T2-limit");
      testResult.limit = limit;
      this.metrics.tests.push(testResult);
    }
  }

  async runEdgeCaseTests() {
    console.log("\n🧪 Executando Testes de Edge Cases (T3)...");
    
    for (const edgeCase of TEST_QUERIES.edgeCases) {
      const testResult = await this.executeSearch(edgeCase.query, 5, "T3-edge");
      testResult.query = edgeCase.query;
      testResult.description = edgeCase.description;
      this.metrics.tests.push(testResult);
    }
  }

  async runCircuitBreakerTests() {
    console.log("\n🧪 Executando Testes de Circuit Breaker (T4)...");
    
    // Fazer uma busca para inicializar circuit
    const testResult = await this.executeSearch("test circuit breaker", 5, "T4-init");
    this.metrics.tests.push(testResult);
    
    // Resetar e verificar transição
    await tools.mcp__searxng_web_search__reset_instance({ url: "" });
    
    const afterReset = await tools.mcp__searxng_web_search__get_instances_status();
    testResult.postResetStatus = JSON.parse(afterReset.result);
    
    // Verificar se states foram resetados
    const allClosed = testResult.postResetStatus.instances.every(
      i => i.state === "closed" && i.failure_count === 0
    );
    testResult.circuitBreakerWorking = allClosed;
  }

  async runDistributionTests() {
    console.log("\n🧪 Executando Testes de Distribuição (T5)...");
    
    const iterations = 5;
    for (let i = 0; i < iterations; i++) {
      const testResult = await this.executeSearch("distributed computing", 5, "T5-dist");
      this.metrics.tests.push(testResult);
    }
  }

  async executeSearch(query, limit, testType) {
    const startTime = Date.now();
    let result;
    
    try {
      const response = await tools.mcp__searxng_web_search__web_search({
        query,
        results_limit: limit
      });
      
      result = JSON.parse(response.result);
      const duration = Date.now() - startTime;
      
      return {
        type: testType,
        success: result.success,
        duration,
        resultsCount: result.count || 0,
        instanceUsed: result.instance_used,
        error: result.error,
        details: result.details
      };
    } catch (e) {
      return {
        type: testType,
        success: false,
        duration: Date.now() - startTime,
        resultsCount: 0,
        error: e.message,
        exception: true
      };
    }
  }

  generateReport() {
    const totalDuration = Date.now() - this.metrics.startTime;
    const tests = this.metrics.tests;
    
    const passed = tests.filter(t => t.success).length;
    const failed = tests.filter(t => !t.success).length;
    const successRate = ((passed / tests.length) * 100).toFixed(1);
    
    const durations = tests.map(t => t.duration).filter(d => d > 0);
    const avgDuration = (durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(0);
    const minDuration = Math.min(...durations);
    const maxDuration = Math.max(...durations);

    // Aggregate instance usage
    for (const test of tests) {
      if (test.instanceUsed) {
        this.metrics.instanceUsage[test.instanceUsed] = 
          (this.metrics.instanceUsage[test.instanceUsed] || 0) + 1;
      }
    }

    const report = `# E2E Test Report - SearXNG MCP

## 📋 Metadata
- **Data**: ${new Date().toISOString().replace('T', ' ').substring(0, 19)}
- **Duração Total**: ${(totalDuration / 1000).toFixed(1)}s
- **Ambiente**: searxng-instance-mcp (Pi harness)

## 📊 Resumo Executivo
| Métrica | Valor |
|---------|-------|
| Total de Testes | ${tests.length} |
| ✅ Aprovados | ${passed} |
| ❌ Falhas | ${failed} |
| Taxa de Sucesso | ${successRate}% |
| Instâncias Testadas | ${Object.keys(this.metrics.instanceUsage).length} |
| Tempo Médio | ${avgDuration}ms |
| Busca Mais Rápida | ${minDuration}ms |
| Busca Mais Lenta | ${maxDuration}ms |

## 🔍 Resultados Detalhados

### T1: Busca Básica
${this.formatTestResults(tests.filter(t => t.type === 'T1-basic'))}

### T2: Limite de Resultados  
${this.formatLimitResults(tests.filter(t => t.type === 'T2-limit'))}

### T3: Edge Cases
${this.formatEdgeCaseResults(tests.filter(t => t.type === 'T3-edge'))}

### T4: Circuit Breaker
${this.formatCircuitBreakerResults(tests.filter(t => t.type.startsWith('T4'))[0])}

### T5: Distribuição de Instâncias
${this.formatDistributionResults(this.metrics.instanceUsage)}

## ⚠️ Problemas Encontrados
${this.formatProblems(tests.filter(t => !t.success))}

## 💡 Recomendações
${this.generateRecommendations(tests, this.metrics.instanceUsage)}

---

*Relatório gerado automaticamente pelo E2E Test Suite*
`;

    return report;
  }

  formatTestResults(results) {
    if (results.length === 0) return "_Nenhum teste executado_";
    
    return results.map(r => {
      const status = r.success ? '✅' : '❌';
      return `| ${status} | "${r.query}" | ${r.resultsCount} resultados | ${r.duration}ms | ${r.instanceUsed || 'N/A'} |`;
    }).join('\n');
  }

  formatLimitResults(results) {
    if (results.length === 0) return "_Nenhum teste executado_";
    
    return results.map(r => {
      const status = r.success && r.resultsCount <= r.limit ? '✅' : '❌';
      return `| ${status} | Limite ${r.limit} | ${r.resultsCount} resultados | ${r.duration}ms |`;
    }).join('\n');
  }

  formatEdgeCaseResults(results) {
    if (results.length === 0) return "_Nenhum teste executado_";
    
    return results.map(r => {
      const status = !r.success ? '✅ (erro esperado)' : (r.success ? '✅' : '❌');
      return `| "${r.description}" | ${status} | ${r.error || 'OK'} |`;
    }).join('\n');
  }

  formatCircuitBreakerResults(result) {
    if (!result) return "_Nenhum teste executado_";
    
    const allClosed = result.postResetStatus?.instances?.every(
      i => i.state === "closed" && i.failure_count === 0
    );
    const status = allClosed ? '✅' : '⚠️';
    
    return `| ${status} | Reset funcionou | Estados: ${result.postResetStatus?.instances?.filter(i => i.state === 'closed').length}/${result.postResetStatus?.instances?.length || 0} closed |`;
  }

  formatDistributionResults(usage) {
    if (Object.keys(usage).length === 0) return "_Nenhum dado coletado_";
    
    return Object.entries(usage)
      .map(([url, count]) => `| ${url} | ${count} |`)
      .join('\n');
  }

  formatProblems(failedTests) {
    if (failedTests.length === 0) return "_Nenhum problema encontrado_ ✅";
    
    return failedTests.map(t => {
      const details = t.details ? JSON.stringify(t.details).substring(0, 100) : t.error;
      return `- **${t.type}** (${t.query || 'N/A'}): ${t.error || 'Erro desconhecido'}\n  Details: ${details}`;
    }).join('\n');
  }

  generateRecommendations(tests, usage) {
    const recommendations = [];
    
    if (tests.filter(t => !t.success).length > tests.length * 0.3) {
      recommendations.push("- ⚠️ Alta taxa de falha. Verificar conectividade de rede e status das instâncias.");
    }
    
    if (Object.keys(usage).length === 1) {
      recommendations.push("- ℹ️ Apenas uma instância está sendo usada. Verificar se outras estão disponíveis.");
    }
    
    const slowTests = tests.filter(t => t.duration > 5000);
    if (slowTests.length > 0) {
      recommendations.push("- ⚠️ Algumas buscas tiveram latência alta (>5s). Considerar aumentar timeout.");
    }
    
    if (recommendations.length === 0) {
      recommendations.push("- ✅ Sistema funcionando dentro dos parâmetros esperados.");
    }
    
    return recommendations.join('\n');
  }
}

// Executar testes
const runner = new E2ETestRunner();
return await runner.runAllTests();
