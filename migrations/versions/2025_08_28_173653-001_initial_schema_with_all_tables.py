"""Initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2025-08-28 17:36:53.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create tables ###
    
    # Sites table
    op.create_table('sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('api_endpoints', sa.JSON(), nullable=False),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False),
        sa.Column('request_timeout_ms', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('retry_delay_ms', sa.Integer(), nullable=False),
        sa.Column('requires_auth', sa.Boolean(), nullable=False),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=10), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_successful_collection', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_error_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sites_created_at'), 'sites', ['created_at'], unique=False)
    op.create_index(op.f('ix_sites_id'), 'sites', ['id'], unique=False)
    op.create_index(op.f('ix_sites_is_active'), 'sites', ['is_active'], unique=False)
    op.create_index(op.f('ix_sites_is_deleted'), 'sites', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_sites_name'), 'sites', ['name'], unique=True)
    op.create_index(op.f('ix_sites_site_id'), 'sites', ['site_id'], unique=True)
    op.create_index(op.f('ix_sites_updated_at'), 'sites', ['updated_at'], unique=False)

    # Authors table
    op.create_table('authors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('external_author_id', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_url', sa.String(length=500), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('job_title', sa.String(length=200), nullable=True),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('total_articles', sa.Integer(), nullable=False),
        sa.Column('first_article_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_article_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authors_created_at'), 'authors', ['created_at'], unique=False)
    op.create_index(op.f('ix_authors_external_author_id'), 'authors', ['external_author_id'], unique=False)
    op.create_index(op.f('ix_authors_id'), 'authors', ['id'], unique=False)
    op.create_index(op.f('ix_authors_is_deleted'), 'authors', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_authors_name'), 'authors', ['name'], unique=False)
    op.create_index(op.f('ix_authors_site_id'), 'authors', ['site_id'], unique=False)
    op.create_index(op.f('ix_authors_updated_at'), 'authors', ['updated_at'], unique=False)

    # Categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('external_category_id', sa.String(length=100), nullable=True),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('hierarchy_path', sa.String(length=500), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('total_articles', sa.Integer(), nullable=False),
        sa.Column('recent_articles_count', sa.Integer(), nullable=False),
        sa.Column('first_article_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_article_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('trending_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'site_id', name='uq_category_name_site')
    )
    op.create_index(op.f('ix_categories_created_at'), 'categories', ['created_at'], unique=False)
    op.create_index(op.f('ix_categories_external_category_id'), 'categories', ['external_category_id'], unique=False)
    op.create_index(op.f('ix_categories_hierarchy_path'), 'categories', ['hierarchy_path'], unique=False)
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_is_active'), 'categories', ['is_active'], unique=False)
    op.create_index(op.f('ix_categories_is_deleted'), 'categories', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=False)
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.create_index(op.f('ix_categories_site_id'), 'categories', ['site_id'], unique=False)
    op.create_index(op.f('ix_categories_updated_at'), 'categories', ['updated_at'], unique=False)

    # Snapshots table
    op.create_table('snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('request_headers', sa.JSON(), nullable=True),
        sa.Column('request_params', sa.JSON(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('response_headers', sa.JSON(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('response_size_bytes', sa.Integer(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('processed_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('collection_batch_id', sa.String(length=100), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('is_retry', sa.Boolean(), nullable=False),
        sa.Column('parent_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_snapshot_id'], ['snapshots.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_snapshot_batch_timestamp', 'snapshots', ['collection_batch_id', 'timestamp'], unique=False)
    op.create_index('idx_snapshot_site_timestamp', 'snapshots', ['site_id', 'timestamp'], unique=False)
    op.create_index('idx_snapshot_status_timestamp', 'snapshots', ['response_status', 'timestamp'], unique=False)
    op.create_index(op.f('ix_snapshots_collection_batch_id'), 'snapshots', ['collection_batch_id'], unique=False)
    op.create_index(op.f('ix_snapshots_created_at'), 'snapshots', ['created_at'], unique=False)
    op.create_index(op.f('ix_snapshots_endpoint'), 'snapshots', ['endpoint'], unique=False)
    op.create_index(op.f('ix_snapshots_id'), 'snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_snapshots_is_deleted'), 'snapshots', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_snapshots_response_status'), 'snapshots', ['response_status'], unique=False)
    op.create_index(op.f('ix_snapshots_site_id'), 'snapshots', ['site_id'], unique=False)
    op.create_index(op.f('ix_snapshots_timestamp'), 'snapshots', ['timestamp'], unique=False)
    op.create_index(op.f('ix_snapshots_updated_at'), 'snapshots', ['updated_at'], unique=False)

    # Articles table
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('slug', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content_excerpt', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('canonical_url', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('reading_time_minutes', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('topics', sa.JSON(), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=False),
        sa.Column('collection_errors', sa.JSON(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', 'site_id', name='uq_article_external_site')
    )
    op.create_index('idx_article_active_published', 'articles', ['is_active', 'published_at'], unique=False)
    op.create_index('idx_article_site_first_seen', 'articles', ['site_id', 'first_seen'], unique=False)
    op.create_index('idx_article_site_published', 'articles', ['site_id', 'published_at'], unique=False)
    op.create_index(op.f('ix_articles_author_id'), 'articles', ['author_id'], unique=False)
    op.create_index(op.f('ix_articles_category_id'), 'articles', ['category_id'], unique=False)
    op.create_index(op.f('ix_articles_created_at'), 'articles', ['created_at'], unique=False)
    op.create_index(op.f('ix_articles_duplicate_of_id'), 'articles', ['duplicate_of_id'], unique=False)
    op.create_index(op.f('ix_articles_external_id'), 'articles', ['external_id'], unique=False)
    op.create_index(op.f('ix_articles_first_seen'), 'articles', ['first_seen'], unique=False)
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_is_active'), 'articles', ['is_active'], unique=False)
    op.create_index(op.f('ix_articles_is_deleted'), 'articles', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_articles_is_duplicate'), 'articles', ['is_duplicate'], unique=False)
    op.create_index(op.f('ix_articles_last_seen'), 'articles', ['last_seen'], unique=False)
    op.create_index(op.f('ix_articles_published_at'), 'articles', ['published_at'], unique=False)
    op.create_index(op.f('ix_articles_site_id'), 'articles', ['site_id'], unique=False)
    op.create_index(op.f('ix_articles_slug'), 'articles', ['slug'], unique=False)
    op.create_index(op.f('ix_articles_title'), 'articles', ['title'], unique=False)
    op.create_index(op.f('ix_articles_updated_at'), 'articles', ['updated_at'], unique=False)

    # Article History table
    op.create_table('article_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('change_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('change_source', sa.String(length=100), nullable=False),
        sa.Column('change_reason', sa.String(length=200), nullable=True),
        sa.Column('snapshot_id', sa.Integer(), nullable=True),
        sa.Column('change_metadata', sa.JSON(), nullable=True),
        sa.Column('is_significant', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_article_history_article_timestamp', 'article_history', ['article_id', 'change_timestamp'], unique=False)
    op.create_index('idx_article_history_type_timestamp', 'article_history', ['change_type', 'change_timestamp'], unique=False)
    op.create_index(op.f('ix_article_history_article_id'), 'article_history', ['article_id'], unique=False)
    op.create_index(op.f('ix_article_history_change_timestamp'), 'article_history', ['change_timestamp'], unique=False)
    op.create_index(op.f('ix_article_history_change_type'), 'article_history', ['change_type'], unique=False)
    op.create_index(op.f('ix_article_history_created_at'), 'article_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_article_history_id'), 'article_history', ['id'], unique=False)
    op.create_index(op.f('ix_article_history_is_deleted'), 'article_history', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_article_history_is_significant'), 'article_history', ['is_significant'], unique=False)
    op.create_index(op.f('ix_article_history_snapshot_id'), 'article_history', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_article_history_updated_at'), 'article_history', ['updated_at'], unique=False)

    # Collection Stats table
    op.create_table('collection_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=False),
        sa.Column('successful_requests', sa.Integer(), nullable=False),
        sa.Column('failed_requests', sa.Integer(), nullable=False),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('max_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('min_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('total_response_size_bytes', sa.Integer(), nullable=False),
        sa.Column('total_articles_found', sa.Integer(), nullable=False),
        sa.Column('new_articles_created', sa.Integer(), nullable=False),
        sa.Column('existing_articles_updated', sa.Integer(), nullable=False),
        sa.Column('duplicate_articles_found', sa.Integer(), nullable=False),
        sa.Column('processing_errors', sa.Integer(), nullable=False),
        sa.Column('unique_authors_found', sa.Integer(), nullable=False),
        sa.Column('unique_categories_found', sa.Integer(), nullable=False),
        sa.Column('total_word_count', sa.Integer(), nullable=False),
        sa.Column('avg_article_quality_score', sa.Float(), nullable=True),
        sa.Column('error_rate', sa.Float(), nullable=True),
        sa.Column('error_types', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('validation_error_count', sa.Integer(), nullable=False),
        sa.Column('content_freshness_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collection_stats_period_type', 'collection_stats', ['period_type', 'period_start'], unique=False)
    op.create_index('idx_collection_stats_site_period', 'collection_stats', ['site_id', 'period_start', 'period_type'], unique=False)
    op.create_index(op.f('ix_collection_stats_created_at'), 'collection_stats', ['created_at'], unique=False)
    op.create_index(op.f('ix_collection_stats_id'), 'collection_stats', ['id'], unique=False)
    op.create_index(op.f('ix_collection_stats_is_deleted'), 'collection_stats', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_collection_stats_period_end'), 'collection_stats', ['period_end'], unique=False)
    op.create_index(op.f('ix_collection_stats_period_start'), 'collection_stats', ['period_start'], unique=False)
    op.create_index(op.f('ix_collection_stats_period_type'), 'collection_stats', ['period_type'], unique=False)
    op.create_index(op.f('ix_collection_stats_site_id'), 'collection_stats', ['site_id'], unique=False)
    op.create_index(op.f('ix_collection_stats_updated_at'), 'collection_stats', ['updated_at'], unique=False)

    # Site Analytics table (legacy compatibility)
    op.create_table('site_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('total_articles', sa.Integer(), nullable=False),
        sa.Column('new_articles', sa.Integer(), nullable=False),
        sa.Column('unique_authors', sa.Integer(), nullable=False),
        sa.Column('unique_categories', sa.Integer(), nullable=False),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_site_analytics_id'), 'site_analytics', ['id'], unique=False)
    op.create_index(op.f('ix_site_analytics_period_end'), 'site_analytics', ['period_end'], unique=False)
    op.create_index(op.f('ix_site_analytics_period_start'), 'site_analytics', ['period_start'], unique=False)
    op.create_index(op.f('ix_site_analytics_period_type'), 'site_analytics', ['period_type'], unique=False)
    op.create_index(op.f('ix_site_analytics_site_id'), 'site_analytics', ['site_id'], unique=False)


def downgrade() -> None:
    # ### Drop tables ###
    op.drop_index(op.f('ix_site_analytics_site_id'), table_name='site_analytics')
    op.drop_index(op.f('ix_site_analytics_period_type'), table_name='site_analytics')
    op.drop_index(op.f('ix_site_analytics_period_start'), table_name='site_analytics')
    op.drop_index(op.f('ix_site_analytics_period_end'), table_name='site_analytics')
    op.drop_index(op.f('ix_site_analytics_id'), table_name='site_analytics')
    op.drop_table('site_analytics')
    
    op.drop_index(op.f('ix_collection_stats_updated_at'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_site_id'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_period_type'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_period_start'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_period_end'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_is_deleted'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_id'), table_name='collection_stats')
    op.drop_index(op.f('ix_collection_stats_created_at'), table_name='collection_stats')
    op.drop_index('idx_collection_stats_site_period', table_name='collection_stats')
    op.drop_index('idx_collection_stats_period_type', table_name='collection_stats')
    op.drop_table('collection_stats')
    
    op.drop_index(op.f('ix_article_history_updated_at'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_snapshot_id'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_is_significant'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_is_deleted'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_id'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_created_at'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_change_type'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_change_timestamp'), table_name='article_history')
    op.drop_index(op.f('ix_article_history_article_id'), table_name='article_history')
    op.drop_index('idx_article_history_type_timestamp', table_name='article_history')
    op.drop_index('idx_article_history_article_timestamp', table_name='article_history')
    op.drop_table('article_history')
    
    op.drop_index(op.f('ix_articles_updated_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_title'), table_name='articles')
    op.drop_index(op.f('ix_articles_slug'), table_name='articles')
    op.drop_index(op.f('ix_articles_site_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_published_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_last_seen'), table_name='articles')
    op.drop_index(op.f('ix_articles_is_duplicate'), table_name='articles')
    op.drop_index(op.f('ix_articles_is_deleted'), table_name='articles')
    op.drop_index(op.f('ix_articles_is_active'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_first_seen'), table_name='articles')
    op.drop_index(op.f('ix_articles_external_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_duplicate_of_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_created_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_category_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_author_id'), table_name='articles')
    op.drop_index('idx_article_site_published', table_name='articles')
    op.drop_index('idx_article_site_first_seen', table_name='articles')
    op.drop_index('idx_article_active_published', table_name='articles')
    op.drop_table('articles')
    
    op.drop_index(op.f('ix_snapshots_updated_at'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_timestamp'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_site_id'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_response_status'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_is_deleted'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_id'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_endpoint'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_created_at'), table_name='snapshots')
    op.drop_index(op.f('ix_snapshots_collection_batch_id'), table_name='snapshots')
    op.drop_index('idx_snapshot_status_timestamp', table_name='snapshots')
    op.drop_index('idx_snapshot_site_timestamp', table_name='snapshots')
    op.drop_index('idx_snapshot_batch_timestamp', table_name='snapshots')
    op.drop_table('snapshots')
    
    op.drop_index(op.f('ix_categories_updated_at'), table_name='categories')
    op.drop_index(op.f('ix_categories_site_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_parent_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_index(op.f('ix_categories_is_deleted'), table_name='categories')
    op.drop_index(op.f('ix_categories_is_active'), table_name='categories')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_hierarchy_path'), table_name='categories')
    op.drop_index(op.f('ix_categories_external_category_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_created_at'), table_name='categories')
    op.drop_table('categories')
    
    op.drop_index(op.f('ix_authors_updated_at'), table_name='authors')
    op.drop_index(op.f('ix_authors_site_id'), table_name='authors')
    op.drop_index(op.f('ix_authors_name'), table_name='authors')
    op.drop_index(op.f('ix_authors_is_deleted'), table_name='authors')
    op.drop_index(op.f('ix_authors_id'), table_name='authors')
    op.drop_index(op.f('ix_authors_external_author_id'), table_name='authors')
    op.drop_index(op.f('ix_authors_created_at'), table_name='authors')
    op.drop_table('authors')
    
    op.drop_index(op.f('ix_sites_updated_at'), table_name='sites')
    op.drop_index(op.f('ix_sites_site_id'), table_name='sites')
    op.drop_index(op.f('ix_sites_name'), table_name='sites')
    op.drop_index(op.f('ix_sites_is_deleted'), table_name='sites')
    op.drop_index(op.f('ix_sites_is_active'), table_name='sites')
    op.drop_index(op.f('ix_sites_id'), table_name='sites')
    op.drop_index(op.f('ix_sites_created_at'), table_name='sites')
    op.drop_table('sites')