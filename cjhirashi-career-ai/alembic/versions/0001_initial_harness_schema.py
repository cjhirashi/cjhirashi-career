"""initial harness schema

Esquema inicial del harness: las 11 tablas `bedrock_*` de la API (sin FK a users) más
`bedrock_agent_memory` (memoria con full-text), las secuencias de IDs prefijados y el
índice GIN. Generado desde los modelos y revisado a mano; contrato: harness-db-schema.md.

Revision ID: 0001_initial_harness_schema
Revises:
Create Date: 2026-10-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from config import settings

# Secuencias de IDs prefijados (las serial de settings/usage las crea Postgres con la tabla).
PREFIX_SEQUENCES = ("bco_id_seq", "bcm_id_seq", "bct_id_seq", "btk_id_seq", "bam_id_seq")

revision = '0001_initial_harness_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for seq in PREFIX_SEQUENCES:
        op.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1")

    # D-29: búsqueda sin tildes. `unaccent` es trusted (PG13+). La configuración se crea siempre,
    # sea cual sea MEMORY_FTS_CONFIG. CREATE TEXT SEARCH CONFIGURATION no admite IF NOT EXISTS.
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS spanish_unaccent")
    op.execute("CREATE TEXT SEARCH CONFIGURATION spanish_unaccent (COPY = pg_catalog.spanish)")
    op.execute(
        "ALTER TEXT SEARCH CONFIGURATION spanish_unaccent "
        "ALTER MAPPING FOR hword, hword_part, word WITH unaccent, spanish_stem"
    )

    # Idioma del full-text (D-24): se fija al crear la columna generada.
    fts = settings.MEMORY_FTS_CONFIG  # ya validado ([a-z_]+) por Settings; mismo valor que el modelo

    op.create_table('bedrock_agent_delegation',
    sa.Column('profile_id', sa.String(length=50), nullable=False),
    sa.Column('target_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_table('bedrock_agent_memory',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('agent_profile_id', sa.String(length=50), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('search_vector', postgresql.TSVECTOR(), sa.Computed(f"to_tsvector('{fts}'::regconfig, text)", persisted=True), nullable=True),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('source_ref', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'source_ref', name='uq_bedrock_agent_memory_user_source_ref')
    )
    op.create_index('ix_bedrock_agent_memory_search_vector', 'bedrock_agent_memory', ['search_vector'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_bedrock_agent_memory_user_id'), 'bedrock_agent_memory', ['user_id'], unique=False)
    op.create_index('ix_bedrock_agent_memory_user_profile', 'bedrock_agent_memory', ['user_id', 'agent_profile_id'], unique=False)
    op.create_table('bedrock_agent_profile_photos',
    sa.Column('profile_id', sa.String(length=50), nullable=False),
    sa.Column('photo_url', sa.String(length=1024), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_table('bedrock_agent_profile_prompts',
    sa.Column('profile_id', sa.String(length=50), nullable=False),
    sa.Column('system_prompt_suffix', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_table('bedrock_agent_profile_tools',
    sa.Column('profile_id', sa.String(length=50), nullable=False),
    sa.Column('tool_names', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_table('bedrock_conversations',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('session_type', sa.String(length=20), nullable=False),
    sa.Column('agent_profile_id', sa.String(length=50), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bedrock_conversations_agent_profile_id'), 'bedrock_conversations', ['agent_profile_id'], unique=False)
    op.create_index(op.f('ix_bedrock_conversations_session_id'), 'bedrock_conversations', ['session_id'], unique=True)
    op.create_index(op.f('ix_bedrock_conversations_session_type'), 'bedrock_conversations', ['session_type'], unique=False)
    op.create_index(op.f('ix_bedrock_conversations_updated_at'), 'bedrock_conversations', ['updated_at'], unique=False)
    op.create_index(op.f('ix_bedrock_conversations_user_id'), 'bedrock_conversations', ['user_id'], unique=False)
    op.create_index('ix_bedrock_conversations_user_type_profile', 'bedrock_conversations', ['user_id', 'session_type', 'agent_profile_id'], unique=False)
    op.create_table('bedrock_custom_tools',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('headers', sa.JSON(), nullable=True),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('bedrock_settings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('system_prompt', sa.Text(), nullable=True),
    sa.Column('global_rules', sa.Text(), nullable=True),
    sa.Column('active_model_id', sa.String(length=150), nullable=True),
    sa.Column('orchestrator_model_id', sa.String(length=150), nullable=True),
    sa.Column('max_round_trips', sa.Integer(), nullable=False),
    sa.Column('history_window', sa.Integer(), nullable=False),
    sa.Column('daily_budget_usd', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bedrock_tasks',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('assignee_type', sa.String(length=20), nullable=False),
    sa.Column('agent_profile_id', sa.String(length=50), nullable=True),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=False),
    sa.Column('parent_id', sa.String(length=20), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_blocking', sa.Boolean(), nullable=False),
    sa.Column('execute_on_turn', sa.Boolean(), nullable=False),
    sa.Column('turn_notified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('execution_result', sa.Text(), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['bedrock_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bedrock_tasks_assignee_type'), 'bedrock_tasks', ['assignee_type'], unique=False)
    op.create_index(op.f('ix_bedrock_tasks_parent_id'), 'bedrock_tasks', ['parent_id'], unique=False)
    op.create_index('ix_bedrock_tasks_parent_sort', 'bedrock_tasks', ['parent_id', 'sort_order'], unique=False)
    op.create_index(op.f('ix_bedrock_tasks_scheduled_at'), 'bedrock_tasks', ['scheduled_at'], unique=False)
    op.create_index('ix_bedrock_tasks_scheduler', 'bedrock_tasks', ['assignee_type', 'status', 'scheduled_at'], unique=False)
    op.create_index(op.f('ix_bedrock_tasks_status'), 'bedrock_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_bedrock_tasks_user_id'), 'bedrock_tasks', ['user_id'], unique=False)
    op.create_table('bedrock_usage_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('session_id', sa.String(length=64), nullable=False),
    sa.Column('model_id', sa.String(length=150), nullable=False),
    sa.Column('input_tokens', sa.Integer(), nullable=False),
    sa.Column('output_tokens', sa.Integer(), nullable=False),
    sa.Column('cache_read_tokens', sa.Integer(), nullable=False),
    sa.Column('cache_write_tokens', sa.Integer(), nullable=False),
    sa.Column('estimated_cost_usd', sa.Numeric(precision=12, scale=6), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bedrock_usage_logs_created_at'), 'bedrock_usage_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_logs_id'), 'bedrock_usage_logs', ['id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_logs_model_id'), 'bedrock_usage_logs', ['model_id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_logs_session_id'), 'bedrock_usage_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_logs_user_id'), 'bedrock_usage_logs', ['user_id'], unique=False)
    op.create_table('bedrock_usage_round_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=20), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('model_id', sa.String(length=150), nullable=True),
    sa.Column('round_type', sa.String(length=30), nullable=False),
    sa.Column('tool_name', sa.String(length=100), nullable=True),
    sa.Column('agent_profile_id', sa.String(length=50), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=False),
    sa.Column('output_tokens', sa.Integer(), nullable=False),
    sa.Column('cache_read_tokens', sa.Integer(), nullable=False),
    sa.Column('cache_write_tokens', sa.Integer(), nullable=False),
    sa.Column('estimated_cost_usd', sa.Numeric(precision=12, scale=6), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bedrock_usage_round_logs_created_at'), 'bedrock_usage_round_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_round_logs_id'), 'bedrock_usage_round_logs', ['id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_round_logs_model_id'), 'bedrock_usage_round_logs', ['model_id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_round_logs_round_type'), 'bedrock_usage_round_logs', ['round_type'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_round_logs_session_id'), 'bedrock_usage_round_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_bedrock_usage_round_logs_user_id'), 'bedrock_usage_round_logs', ['user_id'], unique=False)
    op.create_table('bedrock_conversation_messages',
    sa.Column('id', sa.String(length=20), nullable=False),
    sa.Column('conversation_id', sa.String(length=20), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['bedrock_conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bedrock_conversation_messages_conversation_id'), 'bedrock_conversation_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bedrock_conversation_messages_conversation_id'), table_name='bedrock_conversation_messages')
    op.drop_table('bedrock_conversation_messages')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_user_id'), table_name='bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_session_id'), table_name='bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_round_type'), table_name='bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_model_id'), table_name='bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_id'), table_name='bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_round_logs_created_at'), table_name='bedrock_usage_round_logs')
    op.drop_table('bedrock_usage_round_logs')
    op.drop_index(op.f('ix_bedrock_usage_logs_user_id'), table_name='bedrock_usage_logs')
    op.drop_index(op.f('ix_bedrock_usage_logs_session_id'), table_name='bedrock_usage_logs')
    op.drop_index(op.f('ix_bedrock_usage_logs_model_id'), table_name='bedrock_usage_logs')
    op.drop_index(op.f('ix_bedrock_usage_logs_id'), table_name='bedrock_usage_logs')
    op.drop_index(op.f('ix_bedrock_usage_logs_created_at'), table_name='bedrock_usage_logs')
    op.drop_table('bedrock_usage_logs')
    op.drop_index(op.f('ix_bedrock_tasks_user_id'), table_name='bedrock_tasks')
    op.drop_index(op.f('ix_bedrock_tasks_status'), table_name='bedrock_tasks')
    op.drop_index('ix_bedrock_tasks_scheduler', table_name='bedrock_tasks')
    op.drop_index(op.f('ix_bedrock_tasks_scheduled_at'), table_name='bedrock_tasks')
    op.drop_index('ix_bedrock_tasks_parent_sort', table_name='bedrock_tasks')
    op.drop_index(op.f('ix_bedrock_tasks_parent_id'), table_name='bedrock_tasks')
    op.drop_index(op.f('ix_bedrock_tasks_assignee_type'), table_name='bedrock_tasks')
    op.drop_table('bedrock_tasks')
    op.drop_table('bedrock_settings')
    op.drop_table('bedrock_custom_tools')
    op.drop_index('ix_bedrock_conversations_user_type_profile', table_name='bedrock_conversations')
    op.drop_index(op.f('ix_bedrock_conversations_user_id'), table_name='bedrock_conversations')
    op.drop_index(op.f('ix_bedrock_conversations_updated_at'), table_name='bedrock_conversations')
    op.drop_index(op.f('ix_bedrock_conversations_session_type'), table_name='bedrock_conversations')
    op.drop_index(op.f('ix_bedrock_conversations_session_id'), table_name='bedrock_conversations')
    op.drop_index(op.f('ix_bedrock_conversations_agent_profile_id'), table_name='bedrock_conversations')
    op.drop_table('bedrock_conversations')
    op.drop_table('bedrock_agent_profile_tools')
    op.drop_table('bedrock_agent_profile_prompts')
    op.drop_table('bedrock_agent_profile_photos')
    op.drop_index('ix_bedrock_agent_memory_user_profile', table_name='bedrock_agent_memory')
    op.drop_index(op.f('ix_bedrock_agent_memory_user_id'), table_name='bedrock_agent_memory')
    op.drop_index('ix_bedrock_agent_memory_search_vector', table_name='bedrock_agent_memory', postgresql_using='gin')
    op.drop_table('bedrock_agent_memory')
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS spanish_unaccent")
    op.drop_table('bedrock_agent_delegation')

    for seq in PREFIX_SEQUENCES:
        op.execute(f"DROP SEQUENCE IF EXISTS {seq}")
