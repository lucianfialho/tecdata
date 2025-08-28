# Railway Deployment Guide - Termômetro de Tecnologia

Este guia detalha como fazer deploy do sistema "Termômetro de Tecnologia" no Railway, incluindo configuração de banco de dados PostgreSQL e execução automática das coletas.

## Visão Geral da Arquitetura Railway

O sistema é deployado como **três serviços separados** no Railway:

1. **Web Service** (`app.py`) - Health checks e API de monitoramento
2. **Worker Service** (`worker.py`) - Coleta automática de dados a cada 4-6 horas
3. **PostgreSQL Database** - Addon do Railway para armazenamento

## Pré-requisitos

- Conta no Railway (https://railway.app)
- Repositório Git configurado
- Código local funcionando (teste com `python main.py`)

## Passo 1: Preparação do Repositório

1. **Commit todos os arquivos de deploy criados:**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Verifique se todos os arquivos estão presentes:**
   - `railway.toml` - Configuração do Railway
   - `Procfile` - Definição dos processos
   - `nixpacks.toml` - Configuração de build
   - `app.py` - Serviço web
   - `worker.py` - Worker de coleta
   - `scripts/deploy.py` - Script de deploy
   - `requirements.txt` - Dependências (com FastAPI/Uvicorn)

## Passo 2: Criação do Projeto no Railway

1. **Acesse Railway e crie novo projeto:**
   - Login em https://railway.app
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Conecte seu repositório

2. **Configure o projeto:**
   - Nome do projeto: `termometro-tecnologia`
   - Branch: `main`

## Passo 3: Configuração do PostgreSQL

1. **Adicionar PostgreSQL addon:**
   - No dashboard do projeto, clique em "New Service"
   - Selecione "Database" → "PostgreSQL"
   - Aguarde a criação (1-2 minutos)

2. **A variável `DATABASE_URL` será automaticamente configurada**

## Passo 4: Configuração dos Serviços

### Web Service (Health Checks)

1. **Configurar serviço web:**
   - Service Name: `tecdata-web`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Port: `8000` (será definido automaticamente)

### Worker Service (Coleta de Dados)

1. **Criar novo serviço:**
   - Clique em "New Service" → "GitHub Repo"
   - Selecione o mesmo repositório
   - Service Name: `tecdata-worker`
   - Start Command: `python worker.py`

## Passo 5: Configuração das Variáveis de Ambiente

Configure as seguintes variáveis para **AMBOS os serviços**:

### Variáveis Obrigatórias:
```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
COLLECTION_INTERVAL_HOURS=4
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRIES=3
BACKOFF_FACTOR=2
REQUESTS_PER_MINUTE=10
MIN_REQUEST_INTERVAL_SECONDS=6
TECMUNDO_API_BASE_URL=https://www.tecmundo.com.br
TECMUNDO_API_ENDPOINT=/api/posts?endpoint=home-author
LOG_FILE_PATH=/tmp/tecdata.log
LOG_ROTATION=1 day
LOG_RETENTION=7 days
```

### Variáveis Automáticas (Railway define):
- `DATABASE_URL` - URL do PostgreSQL
- `PORT` - Porta do serviço web
- `RAILWAY_ENVIRONMENT` - Ambiente Railway

## Passo 6: Deploy e Inicialização

1. **Deploy automático:**
   - Railway fará deploy automaticamente após a configuração
   - Monitor os logs durante o build

2. **Verificar health check:**
   - Acesse: `https://SEU_DOMINIO.railway.app/health`
   - Deve retornar status "healthy" ou "unhealthy" com detalhes

3. **Inicialização manual (se necessário):**
   ```bash
   # Via Railway CLI (opcional)
   railway run python scripts/railway_setup.py
   ```

## Passo 7: Verificação e Monitoramento

### Endpoints de Monitoramento:

- **Health Check:** `/health`
  - Status geral do sistema
  - Conectividade do banco
  - Estatísticas básicas

- **Métricas:** `/metrics`
  - Estatísticas detalhadas
  - Contadores de artigos
  - Informações dos sites

- **Status:** `/status`
  - Status detalhado dos serviços
  - Configurações ativas

### Comandos de Monitoramento:

```bash
# Via Railway CLI
railway run python scripts/monitor.py

# Formato JSON para automação
railway run python scripts/monitor.py --json
```

## Passo 8: Configuração de Domínio (Opcional)

1. **No dashboard Railway:**
   - Vá em Settings do serviço web
   - Configure Custom Domain se desejado
   - O Railway fornece domínio gratuito `*.railway.app`

## Troubleshooting

### Problemas Comuns:

1. **Database connection failed:**
   - Verifique se o PostgreSQL addon está rodando
   - Confirme que `DATABASE_URL` está configurado
   - Verifique logs do serviço de database

2. **Worker não está coletando:**
   - Verifique logs do worker service
   - Confirme que as variáveis de API estão corretas
   - Teste conectividade: `railway run python -c "import requests; print(requests.get('https://www.tecmundo.com.br/api/posts?endpoint=home-author').status_code)"`

3. **Build failures:**
   - Verifique se `requirements.txt` está correto
   - Confirme que `nixpacks.toml` está na raiz
   - Verifique logs de build no Railway

4. **Migration errors:**
   - Execute manualmente: `railway run python scripts/deploy.py`
   - Verifique se Alembic está configurado corretamente

### Logs Importantes:

```bash
# Ver logs do web service
railway logs --service tecdata-web

# Ver logs do worker
railway logs --service tecdata-worker

# Ver logs do database
railway logs --service tecdata-postgres
```

## Configurações de Produção

### Coleta Automática:
- **Intervalo:** 4 horas (configurável via `COLLECTION_INTERVAL_HOURS`)
- **Rate limiting:** 10 requests/minuto
- **Timeout:** 30 segundos por request
- **Retry:** 3 tentativas com backoff exponencial

### Logging:
- **Nível:** INFO (configurável via `LOG_LEVEL`)
- **Rotação:** Diária
- **Retenção:** 7 dias (limitação do Railway)
- **Localização:** `/tmp/tecdata.log`

### Monitoramento:
- Health checks automáticos via `/health`
- Métricas expostas via API
- Logs estruturados

## Custos Estimados

### Railway Free Tier:
- **Execução:** 500h/mês grátis
- **PostgreSQL:** Até 1GB grátis
- **Bandwidth:** 100GB/mês grátis

### Estimativa para este projeto:
- **Web service:** ~720h/mês (sempre rodando)
- **Worker service:** ~720h/mês (sempre rodando)
- **Database:** ~50MB/mês (crescimento gradual)
- **Requests:** ~1,440/mês (coleta a cada 4h)

**Status:** Excederá free tier, custos ~$10-20/mês

## Backup e Manutenção

### Backup Automático:
- Railway faz backup automático do PostgreSQL
- Retenção: 7 dias (free tier)

### Manutenção Regular:
```bash
# Verificar saúde do sistema
railway run python scripts/monitor.py

# Ver estatísticas
curl https://SEU_DOMINIO.railway.app/metrics

# Verificar logs
railway logs --tail
```

## Próximos Passos

Após deploy bem-sucedido:

1. **Configure alertas** (via Railway webhooks ou external monitoring)
2. **Monitore logs** nas primeiras 24h
3. **Verifique coletas** a cada 4-6 horas
4. **Analise dados coletados** via endpoints de API
5. **Considere scaling** se necessário

## Suporte e Debugging

Para debug avançado:
- Use `railway shell` para acesso direto ao container
- Execute `python scripts/monitor.py` para diagnóstico completo
- Monitore métricas via `/metrics` endpoint
- Verifique logs estruturados nos serviços

O sistema deve começar a coletar dados automaticamente após o primeiro deploy bem-sucedido.