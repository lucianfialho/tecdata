# Agentes Especializados por Fase - Termômetro de Tecnologia

## Visão Geral
Este documento define quais agentes Claude serão utilizados em cada fase do projeto, suas responsabilidades específicas e como eles colaborarão para entregar o sistema de análise de tendências tecnológicas.

## Fase 1: Prova de Conceito (Semanas 1-3)

### Agentes Principais
- **rapid-prototyper**
  - Responsabilidade: Setup inicial do projeto e estrutura base
  - Entregáveis: Estrutura de diretórios, Docker Compose, requirements.txt
  - Timing: Semana 1

- **backend-architect**
  - Responsabilidade: Design e implementação do schema PostgreSQL
  - Entregáveis: Migrations, modelos SQLAlchemy, configuração de DB
  - Timing: Semana 1-2

- **test-writer-fixer**
  - Responsabilidade: Testes para validação da coleta de dados
  - Entregáveis: Testes unitários e de integração para coleta
  - Timing: Semana 2-3

### Agentes de Apoio
- **experiment-tracker**: Monitoramento da primeira semana de coleta
- **analytics-reporter**: Análise manual dos padrões encontrados

## Fase 2: Automatização (Semanas 4-7)

### Agentes Principais
- **devops-automator**
  - Responsabilidade: Pipeline automatizado com Apache Airflow
  - Entregáveis: DAGs do Airflow, configuração de containers, CI/CD
  - Timing: Semana 4-5

- **infrastructure-maintainer**
  - Responsabilidade: Monitoramento, logs estruturados e alertas
  - Entregáveis: Sistema de monitoramento, dashboards de saúde
  - Timing: Semana 5-6

- **api-tester**
  - Responsabilidade: Descoberta e validação de APIs de múltiplos sites
  - Entregáveis: Testes automatizados para 3-5 APIs brasileiras
  - Timing: Semana 4-7

- **frontend-developer**
  - Responsabilidade: Dashboard básico para visualização
  - Entregáveis: Interface Streamlit com métricas básicas
  - Timing: Semana 6-7

### Agentes de Apoio
- **backend-architect**: Refinamento do schema para múltiplos sites
- **sprint-prioritizer**: Gestão de prioridades entre as tarefas

## Fase 3: Análise Avançada (Semanas 8-12)

### Agentes Principais
- **ai-engineer**
  - Responsabilidade: Processamento NLP e algoritmos de tendências
  - Entregáveis: Categorização automática com spaCy, detecção de trends
  - Timing: Semana 8-10

- **backend-architect**
  - Responsabilidade: API FastAPI para consulta histórica
  - Entregáveis: API RESTful com documentação, endpoints otimizados
  - Timing: Semana 10-11

- **frontend-developer**
  - Responsabilidade: Interface web avançada de exploração
  - Entregáveis: Dashboard interativo, visualizações de tendências
  - Timing: Semana 11-12

### Agentes de Apoio
- **performance-benchmarker**: Otimização da API (<200ms)
- **test-results-analyzer**: Validação contínua da qualidade dos dados

## Agentes de Apoio Contínuo (Durante todo o projeto)

### **sprint-prioritizer**
- Responsabilidade: Gerenciamento de sprints de 2 semanas
- Atividades: Priorização de features, balanceamento de carga de trabalho
- Frequência: Inicio de cada sprint

### **experiment-tracker**
- Responsabilidade: Tracking de experimentos com APIs e algoritmos
- Atividades: Documentação de testes A/B, métricas de performance
- Frequência: Contínua durante desenvolvimento

### **analytics-reporter**
- Responsabilidade: Relatórios de progresso e métricas de sucesso
- Atividades: Dashboards de KPIs, relatórios semanais
- Frequência: Final de cada semana

### **test-writer-fixer**
- Responsabilidade: Manutenção da qualidade do código
- Atividades: Testes regressivos, cobertura de código
- Frequência: Após cada entrega significativa

## Colaboração Entre Agentes

### Handoffs Críticos
1. **rapid-prototyper → backend-architect**: Estrutura base → Schema de dados
2. **backend-architect → devops-automator**: Schema → Pipeline automatizado  
3. **api-tester → devops-automator**: APIs validadas → Integração no pipeline
4. **ai-engineer → backend-architect**: Modelos NLP → API de consulta
5. **backend-architect → frontend-developer**: API → Interface de usuário

### Sincronização Semanal
- **Segunda-feira**: sprint-prioritizer define prioridades da semana
- **Quarta-feira**: experiment-tracker revisa experimentos em andamento
- **Sexta-feira**: analytics-reporter compila métricas da semana

## Métricas de Sucesso por Agente

### Fase 1
- **rapid-prototyper**: Ambiente local funcionando em <30min setup
- **backend-architect**: Schema suportando coleta contínua sem falhas
- **test-writer-fixer**: 90%+ cobertura de testes na coleta

### Fase 2  
- **devops-automator**: Pipeline com 95%+ uptime
- **infrastructure-maintainer**: Alertas funcionais, zero downtime não detectado
- **api-tester**: 3-5 sites com coleta estável
- **frontend-developer**: Dashboard responsivo e funcional

### Fase 3
- **ai-engineer**: Categorização com 80%+ precisão
- **backend-architect**: API com <200ms response time
- **frontend-developer**: Interface intuitiva e performante
- **performance-benchmarker**: Otimizações mensuráveis implementadas