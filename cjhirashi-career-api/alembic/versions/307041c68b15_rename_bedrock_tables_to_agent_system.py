"""Rename bedrock_* tables to agent_system_* (ADR-024/025).

Desacoplar el nombre del motor de agentes del proveedor Bedrock.
Cambios:
- 10 tablas renombradas: bedrock_* → agent_system_*
- Índices renombrados: ix_bedrock_* → ix_agent_system_*
- Foreign keys y constraints preservados

Revision ID: 307041c68b15
Revises: d1f2a3b4c5e6
Create Date: 2026-08-30 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '307041c68b15'
down_revision = 'd1f2a3b4c5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Renombrar 10 tablas: bedrock_* → agent_system_*
    op.rename_table('bedrock_settings', 'agent_system_settings')
    op.rename_table('bedrock_agent_profile_prompts', 'agent_system_profile_prompts')
    op.rename_table('bedrock_agent_profile_photos', 'agent_system_profile_photos')
    op.rename_table('bedrock_agent_delegation', 'agent_system_delegation')
    op.rename_table('bedrock_custom_tools', 'agent_system_custom_tools')
    op.rename_table('bedrock_conversations', 'agent_system_conversations')
    op.rename_table('bedrock_conversation_messages', 'agent_system_conversation_messages')
    op.rename_table('bedrock_usage_logs', 'agent_system_usage_logs')
    op.rename_table('bedrock_usage_round_logs', 'agent_system_usage_round_logs')
    op.rename_table('bedrock_tasks', 'agent_system_tasks')

    # Renombrar índices para mantener coherencia de nomenclatura
    # Nota: op.rename_index no existe en todas las versiones de Alembic,
    # así que usamos execute() con SQL directo
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_conversations_user_type_profile RENAME TO ix_agent_system_conversations_user_type_profile')
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_conversation_messages_conversation_id RENAME TO ix_agent_system_conversation_messages_conversation_id')
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_tasks_scheduler RENAME TO ix_agent_system_tasks_scheduler')
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_tasks_parent_sort RENAME TO ix_agent_system_tasks_parent_sort')
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_usage_logs_user_id RENAME TO ix_agent_system_usage_logs_user_id')
    op.execute('ALTER INDEX IF EXISTS ix_bedrock_usage_round_logs_user_id RENAME TO ix_agent_system_usage_round_logs_user_id')


def downgrade() -> None:
    # Revertir en orden inverso (índices primero, luego tablas)
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_usage_round_logs_user_id RENAME TO ix_bedrock_usage_round_logs_user_id')
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_usage_logs_user_id RENAME TO ix_bedrock_usage_logs_user_id')
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_tasks_parent_sort RENAME TO ix_bedrock_tasks_parent_sort')
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_tasks_scheduler RENAME TO ix_bedrock_tasks_scheduler')
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_conversation_messages_conversation_id RENAME TO ix_bedrock_conversation_messages_conversation_id')
    op.execute('ALTER INDEX IF EXISTS ix_agent_system_conversations_user_type_profile RENAME TO ix_bedrock_conversations_user_type_profile')

    # Revertir tablas en orden inverso
    op.rename_table('agent_system_tasks', 'bedrock_tasks')
    op.rename_table('agent_system_usage_round_logs', 'bedrock_usage_round_logs')
    op.rename_table('agent_system_usage_logs', 'bedrock_usage_logs')
    op.rename_table('agent_system_conversation_messages', 'bedrock_conversation_messages')
    op.rename_table('agent_system_conversations', 'bedrock_conversations')
    op.rename_table('agent_system_custom_tools', 'bedrock_custom_tools')
    op.rename_table('agent_system_delegation', 'bedrock_agent_delegation')
    op.rename_table('agent_system_profile_photos', 'bedrock_agent_profile_photos')
    op.rename_table('agent_system_profile_prompts', 'bedrock_agent_profile_prompts')
    op.rename_table('agent_system_settings', 'bedrock_settings')
