# Termômetro de Tecnologia - Database Schema

Este documento descreve o schema PostgreSQL completo implementado para o projeto "Termômetro de Tecnologia".

## Visão Geral

O schema foi projetado para:
- Coletar dados de múltiplos sites de tecnologia brasileiros
- Armazenar snapshots brutos das APIs
- Processar e normalizar artigos com tracking temporal
- Gerar métricas agregadas e análises de tendências
- Suportar escalabilidade horizontal e queries otimizadas

## Arquitetura

### Tecnologias
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+ com syntax moderna
- **Migrations**: Alembic
- **Repository Pattern**: Para abstração de dados
- **Soft Deletes**: Suporte em todos os modelos principais

### Características Técnicas
- Timestamps automáticos (created_at, updated_at)
- Soft deletes (is_deleted, deleted_at)
- Índices otimizados para queries temporais
- Constraints de integridade referencial
- Support para JSON fields (flexibilidade futura)
- Views materializadas para analytics

## Tabelas Principais

### 1. Sites
Gerencia os sites de tecnologia que coletamos dados.

```sql
CREATE TABLE sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    site_id VARCHAR(50) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    api_endpoints JSON NOT NULL,
    
    -- Configuração de coleta
    rate_limit_per_hour INTEGER DEFAULT 60,
    request_timeout_ms INTEGER DEFAULT 30000,
    retry_count INTEGER DEFAULT 3,
    retry_delay_ms INTEGER DEFAULT 1000,
    
    -- Autenticação
    requires_auth BOOLEAN DEFAULT FALSE,
    auth_config JSON,
    
    -- Metadata
    description TEXT,
    category VARCHAR(50), -- tech_news, developer_blog, etc.
    country VARCHAR(10) DEFAULT 'BR',
    language VARCHAR(10) DEFAULT 'pt-BR',
    
    -- Status de coleta
    is_active BOOLEAN DEFAULT TRUE,
    last_successful_collection TIMESTAMP WITH TIME ZONE,
    collection_error_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

**Características:**
- Suporte para múltiplas APIs por site
- Configuração flexível de rate limiting
- Health monitoring automático

### 2. Authors
Gerencia autores dos artigos, normalizados por site.

```sql
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    site_id INTEGER REFERENCES sites(id),
    external_author_id VARCHAR(100), -- ID do autor no site original
    
    -- Perfil do autor
    bio TEXT,
    profile_url VARCHAR(500),
    avatar_url VARCHAR(500),
    social_links JSON,
    
    -- Informações profissionais
    email VARCHAR(255),
    job_title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(100),
    
    -- Estatísticas (atualizadas via jobs)
    total_articles INTEGER DEFAULT 0,
    first_article_date TIMESTAMP WITH TIME ZONE,
    last_article_date TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

**Características:**
- Estatísticas calculadas automaticamente
- Suporte para informações de perfil social
- Normalização por site (mesmo autor em sites diferentes = registros separados)

### 3. Categories  
Categorias hierárquicas de artigos por site.

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    site_id INTEGER REFERENCES sites(id),
    external_category_id VARCHAR(100),
    
    -- Display information
    display_name VARCHAR(200),
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50),
    
    -- Hierarquia
    parent_id INTEGER REFERENCES categories(id),
    hierarchy_path VARCHAR(500), -- e.g., "tech/mobile/android"
    level INTEGER DEFAULT 0, -- 0 = root, 1 = child, etc.
    
    -- Configuração
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    -- Estatísticas
    total_articles INTEGER DEFAULT 0,
    recent_articles_count INTEGER DEFAULT 0, -- Últimos 30 dias
    first_article_date TIMESTAMP WITH TIME ZONE,
    last_article_date TIMESTAMP WITH TIME ZONE,
    
    -- Análise de conteúdo
    keywords JSON, -- Keywords associadas para NLP
    trending_score FLOAT DEFAULT 0.0, -- Score de trending calculado
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(name, site_id)
);
```

**Características:**
- Suporte para hierarquias aninhadas
- Score de trending calculado
- Keywords para análise NLP futura

### 4. Articles
Artigos processados com tracking temporal completo.

```sql  
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) NOT NULL,
    
    -- Relacionamentos
    site_id INTEGER REFERENCES sites(id),
    author_id INTEGER REFERENCES authors(id),
    category_id INTEGER REFERENCES categories(id),
    
    -- Conteúdo
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500), -- URL-friendly version
    summary TEXT,
    content_excerpt TEXT, -- Primeiros parágrafos
    
    -- URLs e media
    url TEXT NOT NULL,
    canonical_url TEXT, -- Para detecção de duplicatas
    image_url TEXT,
    images JSON, -- Imagens adicionais
    
    -- Metadata do artigo
    published_at TIMESTAMP WITH TIME ZONE,
    word_count INTEGER,
    reading_time_minutes INTEGER,
    language VARCHAR(10) DEFAULT 'pt-BR',
    
    -- Análise de conteúdo (para NLP futuro)
    tags JSON, -- Tags extraídas
    keywords JSON, -- Keywords extraídas  
    sentiment_score FLOAT, -- -1 to 1
    topics JSON, -- Tópicos extraídos por AI
    
    -- Tracking temporal
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE, -- Quando o conteúdo foi atualizado
    
    -- Status e qualidade
    is_active BOOLEAN DEFAULT TRUE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_id INTEGER REFERENCES articles(id),
    quality_score FLOAT DEFAULT 0.0, -- Score de qualidade 0-100
    
    -- Metadata de coleta
    collection_errors JSON, -- Erros durante coleta
    raw_data JSON, -- Dados originais da API para debug
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(external_id, site_id)
);
```

**Características:**
- Tracking temporal completo (first_seen, last_seen)
- Detecção de duplicatas
- Quality score automático
- Suporte para análise NLP futura
- Raw data preservado para debugging

### 5. Snapshots
Snapshots brutos das APIs com métricas detalhadas.

```sql
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    site_id INTEGER REFERENCES sites(id),
    
    -- Request details  
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) DEFAULT 'GET',
    request_headers JSON,
    request_params JSON,
    
    -- Response details
    response_status INTEGER NOT NULL,
    response_headers JSON,
    response_time_ms INTEGER,
    response_size_bytes INTEGER,
    
    -- Data e processamento
    raw_data JSON NOT NULL,
    processed_count INTEGER DEFAULT 0, -- Items processados
    error_message TEXT,
    
    -- Métricas de qualidade
    data_quality_score FLOAT, -- 0-100 score
    validation_errors JSON, -- Erros de validação de schema
    
    -- Metadata de coleta
    collection_batch_id VARCHAR(100), -- Agrupar snapshots relacionados
    retry_count INTEGER DEFAULT 0,
    is_retry BOOLEAN DEFAULT FALSE,
    parent_snapshot_id INTEGER REFERENCES snapshots(id), -- Para retries
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

**Características:**  
- Métricas detalhadas de performance
- Sistema de retry com parent tracking
- Quality scoring automático
- Batch grouping para coletas relacionadas

### 6. Article History
Tracking de mudanças nos artigos ao longo do tempo.

```sql
CREATE TABLE article_history (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    
    -- Tipo de mudança
    change_type VARCHAR(50) NOT NULL, -- content, metadata, media, analysis, reference
    field_name VARCHAR(100) NOT NULL, -- Campo específico que mudou
    old_value TEXT,
    new_value TEXT,
    
    -- Metadata da mudança
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_source VARCHAR(100) NOT NULL, -- collection, manual_edit, batch_update
    change_reason VARCHAR(200),
    
    -- Contexto adicional
    snapshot_id INTEGER REFERENCES snapshots(id), -- Snapshot que originou a mudança
    change_metadata JSON, -- Contexto adicional
    
    -- Significância da mudança
    is_significant BOOLEAN DEFAULT TRUE, -- Filtrar mudanças menores
    confidence_score FLOAT, -- Confiança na mudança
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

**Características:**
- Tracking granular de mudanças
- Classificação automática de significância  
- Link para snapshot que originou a mudança
- Suporte para diferentes fontes de mudança

### 7. Collection Stats
Estatísticas agregadas de coleta por período.

```sql
CREATE TABLE collection_stats (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES sites(id),
    
    -- Período
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    period_type VARCHAR(20) NOT NULL, -- hour, day, week, month
    
    -- Métricas de coleta
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    max_response_time_ms INTEGER,
    min_response_time_ms INTEGER,
    total_response_size_bytes INTEGER DEFAULT 0,
    
    -- Métricas de processamento
    total_articles_found INTEGER DEFAULT 0,
    new_articles_created INTEGER DEFAULT 0,
    existing_articles_updated INTEGER DEFAULT 0,
    duplicate_articles_found INTEGER DEFAULT 0,
    processing_errors INTEGER DEFAULT 0,
    
    -- Métricas de conteúdo
    unique_authors_found INTEGER DEFAULT 0,
    unique_categories_found INTEGER DEFAULT 0,
    total_word_count INTEGER DEFAULT 0,
    avg_article_quality_score FLOAT,
    
    -- Métricas de erro
    error_rate FLOAT, -- Percentual de requests falhados
    error_types JSON, -- Count de diferentes tipos de erro
    retry_count INTEGER DEFAULT 0,
    
    -- Métricas de qualidade
    data_quality_score FLOAT, -- Score médio de qualidade
    validation_error_count INTEGER DEFAULT 0,
    content_freshness_score FLOAT, -- Quão frescos são os artigos
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

**Características:**
- Agregação por múltiplos períodos (hora, dia, semana, mês)
- Métricas abrangentes de performance e qualidade
- Análise de trends ao longo do tempo

## Índices de Performance

### Índices Básicos (criados pelo Alembic)
- Primary keys automáticos
- Foreign keys indexados
- Campos de status (is_active, is_deleted) indexados
- Timestamps (created_at, updated_at) indexados

### Índices Compostos Especializados

```sql
-- Queries temporais otimizadas
CREATE INDEX idx_articles_site_published ON articles (site_id, published_at DESC);
CREATE INDEX idx_articles_site_first_seen ON articles (site_id, first_seen DESC);
CREATE INDEX idx_articles_active_published ON articles (is_active, published_at DESC);

-- Performance de snapshots
CREATE INDEX idx_snapshot_site_timestamp ON snapshots (site_id, timestamp DESC);
CREATE INDEX idx_snapshot_status_timestamp ON snapshots (response_status, timestamp DESC);
CREATE INDEX idx_snapshot_batch_timestamp ON snapshots (collection_batch_id, timestamp DESC);

-- Analytics otimizadas
CREATE INDEX idx_collection_stats_site_period ON collection_stats (site_id, period_start DESC, period_type);

-- Text search (com extensão pg_trgm)
CREATE INDEX idx_articles_title_trgm ON articles USING gin (title gin_trgm_ops);
CREATE INDEX idx_articles_summary_trgm ON articles USING gin (summary gin_trgm_ops);
```

## Views Analíticas

### article_summary
Visão completa de artigos com dados relacionados.

```sql  
CREATE VIEW article_summary AS
SELECT 
    a.id, a.external_id, a.title, a.url,
    a.published_at, a.first_seen, a.last_seen,
    a.word_count, a.quality_score,
    a.is_active, a.is_duplicate,
    s.name as site_name, s.site_id,
    au.name as author_name,
    c.name as category_name,
    c.display_name as category_display_name
FROM articles a
LEFT JOIN sites s ON a.site_id = s.id
LEFT JOIN authors au ON a.author_id = au.id  
LEFT JOIN categories c ON a.category_id = c.id
WHERE a.is_deleted = false;
```

### site_health
Métricas de saúde dos sites.

```sql
CREATE VIEW site_health AS
SELECT 
    s.id, s.name, s.site_id, s.is_active,
    s.collection_error_count, s.last_successful_collection,
    COUNT(DISTINCT a.id) as total_articles,
    COUNT(DISTINCT CASE WHEN a.first_seen >= NOW() - INTERVAL '24 hours' THEN a.id END) as articles_last_24h,
    COUNT(DISTINCT au.id) as total_authors,
    COUNT(DISTINCT c.id) as total_categories,
    AVG(a.quality_score) as avg_quality_score,
    MAX(a.last_seen) as last_article_seen
FROM sites s
LEFT JOIN articles a ON s.id = a.site_id AND a.is_deleted = false
LEFT JOIN authors au ON s.id = au.site_id AND au.is_deleted = false
LEFT JOIN categories c ON s.id = c.site_id AND c.is_deleted = false
WHERE s.is_deleted = false
GROUP BY s.id, s.name, s.site_id, s.is_active, s.collection_error_count, s.last_successful_collection;
```

## Funções PostgreSQL

### get_article_stats()
Estatísticas de artigos para um período.

```sql
CREATE FUNCTION get_article_stats(
    p_site_id INTEGER DEFAULT NULL,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '7 days',
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) RETURNS TABLE(...);
```

### cleanup_old_snapshots()
Limpeza automática de snapshots antigos.

```sql
CREATE FUNCTION cleanup_old_snapshots(
    p_days_to_keep INTEGER DEFAULT 90
) RETURNS INTEGER;
```

### update_author_stats()
Atualização em batch das estatísticas de autores.

```sql  
CREATE FUNCTION update_author_stats(
    p_site_id INTEGER DEFAULT NULL
) RETURNS INTEGER;
```

## Repository Pattern

### BaseRepository
Classe base com CRUD genérico:

```python
class BaseRepository(Generic[T]):
    def create(self, **kwargs) -> T
    def get_by_id(self, id: int) -> Optional[T]  
    def get_all(self, limit: int = None, offset: int = None) -> List[T]
    def update(self, id: int, **kwargs) -> Optional[T]
    def delete(self, id: int, soft_delete: bool = True) -> bool
    def search(self, search_term: str, fields: List[str]) -> List[T]
    def bulk_create(self, records: List[Dict[str, Any]]) -> List[T]
```

### Repositories Especializados
- **SiteRepository**: Gerenciamento de sites
- **SnapshotRepository**: Snapshots com métricas de performance  
- **ArticleRepository**: Artigos com detecção de duplicatas
- **AuthorRepository**: Autores com estatísticas
- **CategoryRepository**: Categorias hierárquicas
- **CollectionStatsRepository**: Estatísticas agregadas

## Setup e Inicialização

### 1. Migrations com Alembic
```bash
# Criar migração inicial
alembic revision --autogenerate -m "Initial schema"

# Aplicar migrações
alembic upgrade head
```

### 2. Script de Inicialização
```bash
# Inicialização completa
python scripts/init_db.py

# Reset completo
python scripts/init_db.py --reset

# Apenas seed data
python scripts/init_db.py --seed-only
```

### 3. Validação
O script de inicialização inclui validação automática:
- Conectividade com o banco
- Funcionamento dos repositories
- Execução das funções PostgreSQL
- Integridade dos dados seed

## Dados Seed

### Site Tecmundo
- Configuração completa para coleta
- Endpoints da API mapeados
- Rate limiting configurado
- Categorias padrão criadas

### Categorias Padrão
- tecnologia, smartphones, games
- ciencia, internet, gadgets
- Configuradas com display names e descrições

## Considerações de Performance

### Particionamento Futuro
Tabelas preparadas para particionamento:
- **snapshots**: Por timestamp (mensal)
- **article_history**: Por timestamp (mensal)
- **collection_stats**: Por period_start (anual)

### Caching Strategy
- Views materializadas para analytics
- Estatísticas calculadas em background jobs
- Cache de queries frequentes no application layer

### Monitoramento
- Métricas de coleta em tempo real
- Health checks automáticos de sites
- Alertas por email para falhas recorrentes

## Próximos Passos

1. **Implementar pipeline de NLP** para análise de conteúdo
2. **Adicionar mais sites** brasileiros de tecnologia
3. **Criar API GraphQL** para consulta de dados
4. **Implementar dashboard** com Streamlit
5. **Setup de produção** com Docker e CI/CD

Este schema fornece uma base sólida e escalável para o projeto "Termômetro de Tecnologia", permitindo coleta eficiente, análise temporal e geração de insights sobre o ecossistema de tecnologia brasileiro.