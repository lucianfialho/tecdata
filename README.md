# Termômetro de Tecnologia

Sistema para capturar, armazenar e analisar dados históricos de conteúdo de sites de tecnologia brasileiros, criando insights sobre tendências e ciclos de tópicos no setor.

## 🚀 Quick Start (< 30 minutos)

### Pré-requisitos

- Python 3.9+
- Docker e Docker Compose
- Git

### Setup do Ambiente Local

1. **Clone e configure o projeto:**
   ```bash
   cd tecdata
   cp .env.example .env
   ```

2. **Instale as dependências Python:**
   ```bash
   # Recomendado: criar um ambiente virtual
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   
   pip install -r requirements.txt
   ```

3. **Inicie o banco de dados:**
   ```bash
   docker-compose up -d
   ```

4. **Teste o setup:**
   ```bash
   python main.py
   ```

### Verificação da Instalação

Se tudo estiver funcionando, você verá:
- ✓ Database connection successful
- ✓ Database initialized successfully  
- ✓ Tecmundo collection successful

### Acesso ao Banco

- **Adminer**: http://localhost:8080
  - Sistema: PostgreSQL
  - Servidor: postgres
  - Usuário: tecdata_user
  - Senha: tecdata_pass
  - Base: tecdata

## 📁 Estrutura do Projeto

```
tecdata/
├── src/                    # Código fonte principal
│   ├── collectors/         # Coletores para diferentes sites
│   │   ├── base.py        # Classe base para coletores
│   │   └── tecmundo.py    # Coletor do Tecmundo
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── base.py        # Configuração base do banco
│   │   ├── snapshots.py   # Snapshots das APIs
│   │   ├── articles.py    # Artigos processados
│   │   └── site_analytics.py # Métricas agregadas
│   └── utils/             # Utilitários
│       ├── logger.py      # Configuração de logs
│       ├── http_client.py # Cliente HTTP com retry
│       └── database.py    # Gerenciamento do banco
├── config/                # Configurações
│   └── settings.py        # Settings usando Pydantic
├── tests/                 # Testes
├── data/                  # Dados locais e SQL
├── logs/                  # Logs da aplicação
├── docker-compose.yml     # Ambiente de desenvolvimento
├── requirements.txt       # Dependências Python
└── main.py               # Script principal de teste
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

Copie `.env.example` para `.env` e ajuste conforme necessário:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=tecdata
POSTGRES_USER=tecdata_user
POSTGRES_PASSWORD=tecdata_pass

# Collection
COLLECTION_INTERVAL_HOURS=6
REQUESTS_PER_MINUTE=10

# Logging
LOG_LEVEL=INFO
```

### Adicionando Novos Sites

1. Crie um novo coletor em `src/collectors/`
2. Herde de `BaseCollector`
3. Implemente `get_api_url()` e `parse_response()`
4. Adicione configurações específicas em `config/settings.py`

## 📊 Uso

### Coleta Manual de Dados

```python
from src.collectors.tecmundo import TecmundoCollector

with TecmundoCollector() as collector:
    success = collector.collect_data()
```

### Consulta de Dados

```python
from src.utils.database import DatabaseManager
from src.models.articles import Article

with DatabaseManager.get_session() as session:
    articles = session.query(Article).limit(10).all()
    for article in articles:
        print(f"{article.title} - {article.site_id}")
```

## 🚧 Roadmap

### Fase 1: MVP (2-3 semanas) ✅
- [x] Script Python básico para coleta do Tecmundo
- [x] Schema PostgreSQL inicial
- [ ] Captura de dados por 1 semana
- [ ] Análise manual dos padrões

### Fase 2: Automatização (3-4 semanas)
- [ ] Pipeline automatizado com Airflow
- [ ] Sistema de monitoramento
- [ ] Integração com mais sites
- [ ] Dashboard básico

### Fase 3: Análise Avançada (4-6 semanas)
- [ ] Processamento NLP
- [ ] Detecção de tendências
- [ ] API para consulta de dados
- [ ] Interface web

## 🛠️ Desenvolvimento

### Executar Testes

```bash
pytest tests/
```

### Formatação de Código

```bash
black src/
isort src/
flake8 src/
```

### Logs

Logs são salvos em `logs/tecdata.log` com rotação diária.

### Parar Ambiente

```bash
docker-compose down
```

## 📝 Licença

Este projeto é para fins de aprendizado e desenvolvimento de competências técnicas.

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request