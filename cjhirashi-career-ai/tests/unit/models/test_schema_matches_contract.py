"""RF-006: los metadatos SQLAlchemy coinciden con contracts/harness-db-schema.md §1 (T-014)."""
import pytest
from sqlalchemy.dialects import postgresql

T = "TIMESTAMP WITH TIME ZONE"
V = "VARCHAR"

# tabla -> {columna: (tipo PG, not_null)}   (`!` del contrato = True)
CONTRACT = {
    "bedrock_agent_delegation": {
        "profile_id": (f"{V}(50)", True), "target_ids": ("JSONB", True), "updated_at": (T, True)},
    "bedrock_agent_profile_photos": {
        "profile_id": (f"{V}(50)", True), "photo_url": (f"{V}(1024)", True), "updated_at": (T, True)},
    "bedrock_agent_profile_prompts": {
        "profile_id": (f"{V}(50)", True), "system_prompt_suffix": ("TEXT", True), "updated_at": (T, True)},
    "bedrock_agent_profile_tools": {
        "profile_id": (f"{V}(50)", True), "tool_names": ("JSONB", False), "updated_at": (T, True)},
    "bedrock_conversations": {
        "id": (f"{V}(20)", True), "user_id": (f"{V}(20)", True), "session_id": (f"{V}(100)", True),
        "session_type": (f"{V}(20)", True), "agent_profile_id": (f"{V}(50)", False),
        "title": (f"{V}(255)", True), "created_at": (T, True), "updated_at": (T, True)},
    "bedrock_conversation_messages": {
        "id": (f"{V}(20)", True), "conversation_id": (f"{V}(20)", True), "role": (f"{V}(20)", True),
        "content": ("TEXT", True), "created_at": (T, True)},
    "bedrock_custom_tools": {
        "id": (f"{V}(20)", True), "name": (f"{V}(100)", True), "url": ("TEXT", True),
        "headers": ("JSON", False), "is_enabled": ("BOOLEAN", True), "created_at": (T, True)},
    "bedrock_settings": {
        "id": ("INTEGER", True), "system_prompt": ("TEXT", False), "global_rules": ("TEXT", False),
        "active_model_id": (f"{V}(150)", False), "orchestrator_model_id": (f"{V}(150)", False),
        "max_round_trips": ("INTEGER", True), "history_window": ("INTEGER", True),
        "daily_budget_usd": ("NUMERIC(10, 4)", True), "updated_at": (T, True)},
    "bedrock_tasks": {
        "id": (f"{V}(20)", True), "user_id": (f"{V}(20)", True), "title": (f"{V}(255)", True),
        "description": ("TEXT", False), "status": (f"{V}(20)", True), "notes": ("TEXT", False),
        "assignee_type": (f"{V}(20)", True), "agent_profile_id": (f"{V}(50)", False),
        "scheduled_at": (T, False), "due_at": (T, False), "priority": (f"{V}(20)", True),
        "parent_id": (f"{V}(20)", False), "sort_order": ("INTEGER", True),
        "is_blocking": ("BOOLEAN", True), "execute_on_turn": ("BOOLEAN", True),
        "turn_notified_at": (T, False), "execution_result": ("TEXT", False),
        "executed_at": (T, False), "error_message": ("TEXT", False),
        "created_at": (T, True), "updated_at": (T, True)},
    "bedrock_usage_logs": {
        "id": ("INTEGER", True), "user_id": (f"{V}(20)", True), "session_id": (f"{V}(64)", True),
        "model_id": (f"{V}(150)", True), "input_tokens": ("INTEGER", True),
        "output_tokens": ("INTEGER", True), "cache_read_tokens": ("INTEGER", True),
        "cache_write_tokens": ("INTEGER", True), "estimated_cost_usd": ("NUMERIC(12, 6)", True),
        "created_at": (T, True)},
    "bedrock_usage_round_logs": {
        "id": ("INTEGER", True), "user_id": (f"{V}(20)", True), "session_id": (f"{V}(100)", True),
        "model_id": (f"{V}(150)", False), "round_type": (f"{V}(30)", True),
        "tool_name": (f"{V}(100)", False), "agent_profile_id": (f"{V}(50)", False),
        "input_tokens": ("INTEGER", True), "output_tokens": ("INTEGER", True),
        "cache_read_tokens": ("INTEGER", True), "cache_write_tokens": ("INTEGER", True),
        "estimated_cost_usd": ("NUMERIC(12, 6)", True), "notes": ("TEXT", False),
        "created_at": (T, True)},
    "bedrock_agent_memory": {
        "id": (f"{V}(20)", True), "user_id": (f"{V}(20)", True), "kind": (f"{V}(20)", True),
        "agent_profile_id": (f"{V}(50)", False), "text": ("TEXT", True),
        "search_vector": ("TSVECTOR", False), "source": (f"{V}(20)", True),
        "source_ref": (f"{V}(100)", False), "created_at": (T, True)},
}

# FK conservadas (tabla, columna) -> (destino, ondelete)
FKS = {
    ("bedrock_conversation_messages", "conversation_id"): ("bedrock_conversations.id", "CASCADE"),
    ("bedrock_tasks", "parent_id"): ("bedrock_tasks.id", "CASCADE"),
}

PK_SINGLE = {t: ("id" if "id" in cols else "profile_id") for t, cols in CONTRACT.items()}


@pytest.fixture(scope="module")
def tables():
    import models  # noqa: F401  (registra los modelos en Base.metadata)
    from database import Base

    return Base.metadata.tables


@pytest.mark.requisito("RF-006")
def test_metadata_has_exactly_the_12_contract_tables(tables):
    assert set(tables) == set(CONTRACT)
    assert len(tables) == 12


@pytest.mark.requisito("RF-006")
@pytest.mark.parametrize("table", sorted(CONTRACT))
def test_columns_types_and_nullability_match_contract(tables, table):
    actual = {
        c.name: (c.type.compile(dialect=postgresql.dialect()), not c.nullable)
        for c in tables[table].columns
    }
    assert actual == CONTRACT[table]


@pytest.mark.requisito("RF-006")
@pytest.mark.parametrize("table", sorted(CONTRACT))
def test_primary_key_matches_contract(tables, table):
    assert [c.name for c in tables[table].primary_key.columns] == [PK_SINGLE[table]]


@pytest.mark.requisito("RF-006")
def test_only_contract_foreign_keys_and_none_to_users(tables):
    found = {}
    for name, table in tables.items():
        for fk in table.foreign_keys:
            assert fk.column.table.name != "users", f"{name}.{fk.parent.name} apunta a users"
            found[(name, fk.parent.name)] = (fk.target_fullname, fk.ondelete)
    assert found == FKS


@pytest.mark.requisito("RF-006")
def test_user_id_columns_are_indexed(tables):
    for name, table in tables.items():
        if "user_id" in table.c:
            assert table.c.user_id.index or any(
                [c.name for c in ix.columns][0] == "user_id" for ix in table.indexes
            ), f"{name}.user_id sin índice"
