# Semana 1 - Setup Inicial e Prova de Conceito

## Agentes Responsáveis
- **Primário**: rapid-prototyper
- **Secundário**: backend-architect
- **Apoio**: sprint-prioritizer

## Objetivos da Semana
- [ ] Configurar ambiente de desenvolvimento completo
- [ ] Implementar coleta básica da API do Tecmundo
- [ ] Criar schema PostgreSQL inicial
- [ ] Primeira execução de coleta de dados

## Tasks Detalhadas

### Task 1.1: Setup do Ambiente (rapid-prototyper)
**Prioridade**: Alta  
**Estimativa**: 4-6 horas  
**Agente**: rapid-prototyper

#### Subtasks:
- [ ] Criar estrutura de diretórios do projeto
- [ ] Configurar Docker Compose com PostgreSQL
- [ ] Setup do ambiente Python (requirements.txt, venv)
- [ ] Configurar variables de ambiente (.env template)

#### Critérios de Aceitação:
- Docker Compose sobe PostgreSQL sem erros
- Ambiente Python ativo com dependências instaladas
- Documentação de setup no README

### Task 1.2: Schema PostgreSQL Inicial (backend-architect)
**Prioridade**: Alta  
**Estimativa**: 3-4 horas  
**Agente**: backend-architect

#### Subtasks:
- [ ] Criar tabela `snapshots` (timestamp, site_id, raw_data)
- [ ] Criar tabela `articles` (id, title, author, category, first_seen, last_seen)
- [ ] Criar tabela `sites` (id, name, api_endpoint, last_collection)
- [ ] Setup SQLAlchemy models
- [ ] Criar migrations iniciais

#### Critérios de Aceitação:
- Schema criado via migration
- Models SQLAlchemy funcionais
- Conexão com PostgreSQL validada

### Task 1.3: Coleta Básica Tecmundo (rapid-prototyper)
**Prioridade**: Alta  
**Estimativa**: 4-5 horas  
**Agente**: rapid-prototyper

#### Subtasks:
- [ ] Implementar cliente HTTP para API Tecmundo
- [ ] Parsear resposta JSON da API
- [ ] Salvar dados brutos na tabela `snapshots`
- [ ] Extrair artigos individuais na tabela `articles`
- [ ] Implementar logging estruturado

#### Critérios de Aceitação:
- Script coleta dados da API sem erros
- Dados salvos corretamente no PostgreSQL  
- Logs informativos sobre coleta

### Task 1.4: Primeira Execução e Validação (sprint-prioritizer)
**Prioridade**: Média  
**Estimativa**: 2-3 horas  
**Agente**: sprint-prioritizer

#### Subtasks:
- [ ] Executar primeira coleta completa
- [ ] Validar dados coletados no database
- [ ] Documentar estrutura de dados encontrada
- [ ] Identificar possíveis inconsistências

#### Critérios de Aceitação:
- Pelo menos 20 artigos coletados com sucesso
- Dados estruturados validados
- Report de qualidade dos dados

## Blockers Potenciais
- **API do Tecmundo indisponível**: Implementar retry logic básico
- **Problemas de conexão PostgreSQL**: Validar configuração Docker
- **Rate limiting da API**: Implementar delays entre requests

## Entregáveis da Semana
1. **Código**: Repositório funcional com coleta básica
2. **Infraestrutura**: Docker Compose funcional
3. **Dados**: Primeira amostra de artigos coletados
4. **Documentação**: README com instruções de setup

## Definição de Pronto
- [ ] Ambiente local reproduzível em <30 min
- [ ] Coleta automatizada funcional
- [ ] Schema PostgreSQL estável
- [ ] Pelo menos 50 artigos coletados
- [ ] Código versionado no Git

## Handoff para Semana 2
- **Para backend-architect**: Schema validado e pronto para extensão
- **Para test-writer-fixer**: Código estável pronto para testes
- **Para experiment-tracker**: Primeira semana de dados para análise