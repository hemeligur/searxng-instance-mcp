# SearXNG Local (Docker)

[![🇺🇸 English](./searxng-local-en.md)](./searxng-local-en.md)

Este documento explica como rodar uma instância SearXNG localmente, caso você precise de **máxima privacidade** ou prefira não depender de instâncias públicas.

> ⚠️ **Este MCP não gerencia instâncias locais.** Ele é um cliente que se conecta a instâncias públicas在线. Para rodar localmente, use as opções abaixo.

---

## Opção 1: Docker Compose (Recomendado)

### Instalação

```bash
# Clone o repositório oficial
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker

# Edite o arquivo .env com suas configurações
cp .env.template .env

# Inicie o container
docker-compose up -d
```

### Configuração

Edite `searxng/data/ultralist.yml` para configurar os motores de busca.

### Acesso

- Interface web: http://localhost:8888
- API JSON: http://localhost:8888/search?q=test&format=json

---

## Opção 2: Instalação Manual

### Pré-requisitos

- Python 3.10+
- Node.js (opcional, para desenvolvimento)
- nginx (para produção)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/searxng/searxng.git
cd searxng

# Instale dependências
make install

# Instale/uwsgi
make install-pyenv

# Configuração
cp searxng/settings.yml searxng/settings.yml
nano searxng/settings.yml

# Execute
make run
```

---

## Opção 3: SearXNG-ng (fork alternativo)

```bash
# Clone
git clone https://github.com/searxng/searxng.git searxng-data

# Use o script de setup
bash -c "$(curl - https://raw.githubusercontent.com/searxng/searxng-docker/master/run.sh)"
```

---

## Configurações Importantes

### Settings.yml

```yaml
search:
  formats:
    - html
    - json

server:
  secret_key: "change-me-to-something-random"
  bind:
    - "0.0.0.0:8888"

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
```

### Desabilitar Logging

```yaml
general:
  instance_name: "my-searxng"
  privacypolicy_url: false
  donation_url: false
  contact_url: false
  enable_metrics: false
```

---

## Comparação: Cliente MCP vs Instância Local

| Aspecto | Este MCP (Cliente) | Instância Local |
|---------|-------------------|-----------------|
| **Privacidade** | Boa (usa instâncias de terceiros) | Máxima (dados nunca saem) |
| **Manutenção** | Zero (gerenciado automaticamente) | Alta (você mantém) |
| **Confiabilidade** | Depende das instâncias públicas | 100% sob seu controle |
| **Recursos** | Baixo (só cliente HTTP) | Alto (nginx, uwsgi, etc.) |
| **Rate Limiting** | Compartilhado com outros | Ilimitado (só você) |

---

## Quando Usar Cada Opção

### Use Este MCP (Cliente)
- ✅ Desenvolvimento rápido
- ✅隐私 é importante mas não crítica
- ✅ Não quer manter infraestrutura
- ✅ Quer fallback automático entre instâncias

### Use Instância Local
- ✅ Privacidade máxima é essencial
- ✅ Quer controle total dos dados
- ✅ Tem conhecimento de Docker/infraestrutura
- ✅ Quer evitar rate limiting

---

## Referências

- Repositório oficial: https://github.com/searxng/searxng
- Docker: https://github.com/searxng/searxng-docker
- Documentação: https://docs.searxng.org
