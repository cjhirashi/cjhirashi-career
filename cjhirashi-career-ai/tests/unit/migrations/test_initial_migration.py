"""RF-006 / RF-022: migración 0001 sobre Postgres real desechable (T-018)."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[3]

TABLES = {
    "bedrock_agent_delegation", "bedrock_agent_profile_photos", "bedrock_agent_profile_prompts",
    "bedrock_agent_profile_tools", "bedrock_conversations", "bedrock_conversation_messages",
    "bedrock_custom_tools", "bedrock_settings", "bedrock_tasks", "bedrock_usage_logs",
    "bedrock_usage_round_logs", "bedrock_agent_memory",
}
SEQUENCES = {
    "bco_id_seq", "bcm_id_seq", "bct_id_seq", "btk_id_seq", "bam_id_seq",
    "bedrock_settings_id_seq", "bedrock_usage_logs_id_seq", "bedrock_usage_round_logs_id_seq",
}


@pytest.fixture
def migrated(pg_url, request):
    """Esquema vaciado + `alembic upgrade head`; devuelve (engine sync, cfg)."""
    from config import settings

    fts = getattr(request, "param", None)
    previous = settings.MEMORY_FTS_CONFIG
    if fts:
        settings.MEMORY_FTS_CONFIG = fts
    sync_url = pg_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", pg_url)
    command.upgrade(cfg, "head")
    yield engine, cfg
    settings.MEMORY_FTS_CONFIG = previous
    engine.dispose()


def _sequences(engine):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT sequencename FROM pg_sequences WHERE schemaname='public'"))
        return {r[0] for r in rows}


@pytest.mark.requisito("RF-006")
def test_upgrade_creates_the_12_tables_and_sequences(migrated):
    engine, _ = migrated
    assert set(inspect(engine).get_table_names()) - {"alembic_version"} == TABLES
    assert SEQUENCES <= _sequences(engine)


@pytest.mark.requisito("RF-006")
def test_migrated_columns_match_model_metadata(migrated):
    import models  # noqa: F401
    from database import Base

    engine, _ = migrated
    insp = inspect(engine)
    from sqlalchemy.dialects import postgresql

    for name, table in Base.metadata.tables.items():
        got = {c["name"]: (c["type"].compile(dialect=postgresql.dialect()), c["nullable"])
               for c in insp.get_columns(name)}
        want = {c.name: (c.type.compile(dialect=postgresql.dialect()), c.nullable)
                for c in table.columns}
        assert got == want, name
    fks = {(t, fk["constrained_columns"][0]): (fk["referred_table"], fk["options"].get("ondelete"))
           for t in TABLES for fk in insp.get_foreign_keys(t)}
    assert fks == {
        ("bedrock_conversation_messages", "conversation_id"): ("bedrock_conversations", "CASCADE"),
        ("bedrock_tasks", "parent_id"): ("bedrock_tasks", "CASCADE"),
    }


@pytest.mark.requisito("RF-022")
def test_search_vector_is_generated_with_gin_index(migrated):
    engine, _ = migrated
    with engine.connect() as conn:
        gen = conn.execute(text(
            "SELECT is_generated, generation_expression FROM information_schema.columns "
            "WHERE table_name='bedrock_agent_memory' AND column_name='search_vector'")).one()
        assert gen[0] == "ALWAYS"
        assert "to_tsvector" in gen[1] and "spanish" in gen[1]
        idx = conn.execute(text(
            "SELECT indexdef FROM pg_indexes WHERE tablename='bedrock_agent_memory' "
            "AND indexdef ILIKE '%USING gin%'")).scalars().all()
        assert any("search_vector" in d for d in idx)


@pytest.mark.requisito("RF-022")
def test_full_text_search_works_in_spanish(migrated):
    engine, _ = migrated
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO bedrock_agent_memory (id, user_id, kind, text, source) "
            "VALUES ('bam-1','usr-1','note','Entrené para varios maratones','harness')"))
        hit = conn.execute(text(
            "SELECT count(*) FROM bedrock_agent_memory "
            "WHERE search_vector @@ websearch_to_tsquery('spanish','maratón')")).scalar()
    assert hit == 1


@pytest.mark.requisito("RF-006")
def test_unique_user_source_ref(migrated):
    engine, _ = migrated
    ins = ("INSERT INTO bedrock_agent_memory (id,user_id,kind,text,source,source_ref) "
           "VALUES ('{i}','usr-1','fact','x','qdrant_import','p-1') ")
    with engine.begin() as conn:
        conn.execute(text(ins.format(i="bam-1")))
    with pytest.raises(Exception, match="uq_bedrock_agent_memory_user_source_ref"):
        with engine.begin() as conn:
            conn.execute(text(ins.format(i="bam-2")))


@pytest.mark.requisito("RF-006")
def test_downgrade_removes_everything(migrated):
    engine, cfg = migrated
    command.downgrade(cfg, "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    assert not (SEQUENCES & _sequences(engine))


def _migrated_expression(engine):
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT generation_expression FROM information_schema.columns "
            "WHERE table_name='bedrock_agent_memory' AND column_name='search_vector'")).scalar_one()


@pytest.mark.requisito("RF-022")
def test_migration_search_vector_expression_equals_model(migrated):
    import models  # noqa: F401
    from database import Base

    engine, _ = migrated
    model_expr = Base.metadata.tables["bedrock_agent_memory"].c.search_vector.computed.sqltext.text
    assert _migrated_expression(engine) == model_expr


@pytest.mark.requisito("RF-022")
@pytest.mark.parametrize("migrated", ["english"], indirect=True)
def test_migration_uses_validated_settings_fts_config(migrated):
    engine, _ = migrated
    assert "'english'::regconfig" in _migrated_expression(engine)
