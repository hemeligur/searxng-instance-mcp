# SearXNG Web Search

Busca na web usando a API JSON do SearXNG.

## Command

```bash
SEARX_URL="https://sx.xo.st"
QUERY='{{query}}'
curl -s "${SEARX_URL}/search?q=${QUERY}&format=json" | head -20
```

## Arguments

- `query`: Termo de busca

## Output

Resultados em JSON com título, URL e descrição.
