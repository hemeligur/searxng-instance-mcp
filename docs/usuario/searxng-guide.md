# Manual: Busca na Web com SearXNG

## O que é SearXNG?

SearXNG é um motor de meta-busca **privado e gratuito** que agrega resultados de diversos buscadores (Google, Bing, DuckDuckGo, etc.) sem rastrear ou perfilar usuários.

---

## Indexador de Instâncias

### 🌐 https://searx.space

Este é o **site oficial** que lista todas as instâncias públicas do SearXNG.

**Dados disponíveis:**
- Status de uptime de cada instância
- Motores de busca habilitados
- Taxa de sucesso por motor
- Localização geográfica dos servidores
- Avaliação de segurança (Mozilla Observatory)

### Como filtrar instâncias boas

No searx.space, procure por instâncias com:
- ✅ **Uptime alto** (>95%)
- ✅ **TLS Grade A+**
- ✅ **Múltiplos motores funcionando** (google, bing, duckduckgo)
- ✅ **Sem rate limiting excessivo**

---

## Instâncias Recomendadas para Teste

| URL | Status | Observações |
|-----|--------|-------------|
| `https://sx.xo.st` | ✅ Boa | Uptime 100%, rápida |
| `https://xka.cz` | ⚠️ Rate limit | Funciona, mas com limites |
| `https://search.ctq.ro` | ✅ Boa | Uptime 100%, TLS A+ |

---

## API JSON do SearXNG

### Endpoint Base

```
GET https://<instancia>/search
```

### Parâmetros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `q` | Query de busca | `q=python+tutorial` |
| `format` | Formato da resposta | `format=json` |
| `engines` | Motores específicos | `engines=google,bing` |
| `lang` | Idioma | `lang=pt-BR` |
| `limit` | Número de resultados | `limit=10` |
| `categories` | Categoria | `categories=general` |

### Exemplo Completo

```bash
curl -s "https://sx.xo.st/search?q=python+programming&format=json&limit=5"
```

### Resposta JSON

```json
{
  "query": "python programming",
  "results": [
    {
      "url": "https://www.python.org/",
      "title": "Welcome to Python.org",
      "content": "Experienced programmers in any other language...",
      "engine": "bing",
      "category": "general"
    }
  ],
  "infoboxes": [],
  "suggestions": [],
  "answers": []
}
```

---

## Como Usar no Pi

### Opção 1: Bash (Direto)

```bash
curl -s "https://sx.xo.st/search?q=termo&format=json"
```

### Opção 2: Skill do Pi

Crie o arquivo `~/.pi/skills/searxng.md`:

```markdown
# SearXNG Web Search

Busca na web usando SearXNG (privacidade-first).

## Command

```bash
curl -s "https://sx.xo.st/search?q={{query}}&format=json"
```

## Arguments

- `query`: Termo de busca (use + para espaços)

## Output

Resultados em JSON com título, URL e descrição.

## Exemplo

Input: `query=javascript framework 2024`
```

Depois recarregue o Pi com `/reload`.

---

## Códigos de Erro Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `Too Many Requests` | Rate limit | Espere ou mude de instância |
| `No result` | IP bloqueado | Tente outra instância |
| `Access denied` | Firewall | Use VPN ou outra instância |
| `Timeout` | Motor sobrecarregado | Repita com motores específicos |

---

## Melhores Práticas

### 1.轮换 de Instâncias

Não abuse de uma única instância. Se receber rate limit:

```bash
# Tente estas em ordem
INSTANCES=("sx.xo.st" "xka.cz" "search.ctq.ro")

for inst in "${INSTANCES[@]}"; do
  result=$(curl -s "https://$inst/search?q=test&format=json")
  if [ -n "$result" ]; then
    echo "$result"
    break
  fi
done
```

### 2. Use Motores Específicos

Se um motor está bloqueado, solicite outros:

```bash
curl "https://sx.xo.st/search?q=test&engines=bing,duckduckgo&format=json"
```

### 3. Evite Buscas Excessivas

O SearXNG é gratuito e mantido por voluntários. Não faça:
- 🔴 Scraping massivo
- 🔴 Automação agressiva
- 🔴 Buscas em loop

---

## Instâncias Públicas Verificadas

### Funcionando em 2026-10-05

```
https://sx.xo.st        # Rápida, bom uptime
https://xka.cz          # Uptime 100%, mas com rate limit
https://www.gruble.de   # Boa para DE
https://www.isci.si     # Backup
```

### Instâncias Confiáveis
```
https://sx.xo.st        # Rápida, bom uptime
https://search.ctq.ro   # Uptime 100%, TLS A+
```

> ⚠️ **Nota**: `https://searxng.org` é o **site oficial/documentação** do projeto, não uma instância pública de busca.

---

## FAQ

**P: É seguro usar instâncias públicas?**
R: Sim. O SearXNG não armazena cookies nem logs. Mas para máxima privacidade, rode sua própria instância.

**P: Por que alguns resultados são duplicados?**
R: A meta-busca agrega de múltiplos motores. Use `engines=` para limitar.

**P: Como encontro instâncias mais rápidas?**
R: Verifique o campo `timing.search` no searx.space. Valores menores = mais rápido.

---

## Referências

- Repositório: https://github.com/searxng/searxng
- Documentação: https://docs.searxng.org
- Instâncias: https://searx.space
- API Search: https://docs.searxng.org/dev/search_api.html
