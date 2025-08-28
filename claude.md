# Termômetro de Tecnologia - Especificações do Projeto

## Visão Geral

Sistema para capturar, armazenar e analisar dados históricos de conteúdo de sites de tecnologia brasileiros, criando insights sobre tendências e ciclos de tópicos no setor.

## Objetivos

### Objetivo Primário
Desenvolver competências técnicas em:
- Engenharia de dados com APIs públicas
- Processamento de dados temporais
- Análise de tendências e padrões

### Objetivos Secundários
- Criar dataset histórico de conteúdo tech brasileiro
- Identificar padrões de propagação de notícias entre sites
- Gerar insights sobre ciclos de hype tecnológico

## Arquitetura Técnica

### Coleta de Dados
- **Fonte inicial**: API do Tecmundo (`/api/posts?endpoint=home-author`)
- **Método**: Requisições HTTP diretas via Python requests
- **Frequência**: A cada 4-6 horas
- **Expansão**: APIs similares de outros sites brasileiros

### Armazenamento
- **Database**: PostgreSQL
- **Schema temporal**: 
  - Tabela `snapshots` (timestamp, site_id, raw_data)
  - Tabela `articles` (id, title, author, category, first_seen, last_seen)
  - Tabela `site_analytics` (métricas agregadas por período)

### Processamento
- **Pipeline**: Python com Apache Airflow para orquestração
- **NLP**: spaCy para extração de tópicos e categorização
- **Análise**: Pandas para processamento de séries temporais

## Implementação por Fases

### Fase 1: Prova de Conceito (2-3 semanas)
- [ ] Script Python básico para coleta do Tecmundo
- [ ] Schema PostgreSQL inicial
- [ ] Captura de dados por 1 semana
- [ ] Análise manual dos padrões encontrados

### Fase 2: Automatização (3-4 semanas)
- [ ] Pipeline automatizado com Airflow
- [ ] Sistema de monitoramento e alertas
- [ ] Descoberta de APIs em 3-5 sites adicionais
- [ ] Dashboard básico para visualização

### Fase 3: Análise Avançada (4-6 semanas)
- [ ] Processamento NLP para categorização automática
- [ ] Algoritmos de detecção de tendências
- [ ] API para consulta dos dados históricos
- [ ] Interface web para exploração de dados

### Fase 4: Produtos de Dados (opcional)
- [ ] Relatórios automatizados
- [ ] Sistema de alertas para tópicos emergentes
- [ ] Comparativo entre sites (competitive intelligence)

## Stack Tecnológico

### Core
- **Linguagem**: Python 3.9+
- **Database**: PostgreSQL 14+
- **Orquestração**: Apache Airflow
- **Containerização**: Docker + Docker Compose

### Bibliotecas Python
- `requests` - HTTP requests
- `sqlalchemy` - ORM e database migrations
- `pandas` - Análise de dados
- `spacy` - Processamento de linguagem natural
- `fastapi` - API para consulta de dados
- `streamlit` - Dashboard e visualização

### Infraestrutura
- **Desenvolvimento**: Local com Docker
- **Produção**: VPS simples (2-4GB RAM)
- **Monitoramento**: Logs estruturados + alertas via email

## Descoberta de APIs

### Sites Alvos
- Tecmundo (confirmado: API pública)
- Olhar Digital
- Canaltech  
- Meio & Mensagem
- IT Forum

### Metodologia
1. Análise de DevTools durante navegação
2. Busca por patterns comuns (`/api/*`, `/wp-json/*`)
3. Teste de endpoints descobertos
4. Documentação de rate limits e estrutura de dados

## Considerações de Risco

### Técnicos
- **Mudanças nas APIs**: Sites podem modificar ou remover endpoints
- **Rate limiting**: Necessidade de implementar backoff e retry logic
- **Qualidade dos dados**: Inconsistências entre sites diferentes

### Legais
- **Termos de uso**: Verificar ToS de cada site
- **Fair use**: Manter frequência de requests conservadora
- **Dados pessoais**: Não coletar informações de usuários

### Operacionais
- **Manutenção**: APIs quebram, sites mudam estrutura
- **Escalabilidade**: Crescimento de dados ao longo do tempo
- **Monitoramento**: Detectar falhas na coleta rapidamente

## Métricas de Sucesso

### Fase 1
- Coleta consistente por 7 dias sem falhas
- Dataset com 100+ artigos únicos
- 3+ padrões identificados manualmente

### Fase 2
- 95%+ uptime do pipeline
- 3-5 sites funcionando simultaneamente
- Dashboard funcional com métricas básicas

### Fase 3
- Categorização automática com 80%+ precisão
- API respondendo em <200ms
- 10+ insights documentados sobre tendências

## Entregáveis

### Código
- Repositório GitHub com documentação completa
- Docker Compose para setup local
- Scripts de migration e backup

### Documentação
- README detalhado
- Guia de setup e deployment
- Documentação da API
- Análise de dados coletados

### Dados
- Dataset histórico em formato aberto
- Relatórios mensais de tendências
- Documentação da metodologia de análise

## Cronograma Estimado

- **Total**: 12-16 semanas
- **MVP funcional**: 6-8 semanas
- **Produto completo**: 12-16 semanas

## Próximos Passos Imediatos

1. Configurar ambiente de desenvolvimento local
2. Implementar coleta básica do Tecmundo
3. Definir schema PostgreSQL inicial
4. Executar primeira semana de coleta
5. Analisar dados coletados manualmente