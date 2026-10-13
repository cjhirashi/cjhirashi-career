"""RF-006: IDs prefijados bco/bcm/bct/btk/bam con nextval en Postgres (T-016)."""
import re

import pytest
from sqlalchemy import text


@pytest.mark.requisito("RF-006")
def test_five_prefixes_are_registered():
    from services.id_generator import TABLE_PREFIXES

    assert TABLE_PREFIXES == {
        "bedrock_conversations": "bco",
        "bedrock_conversation_messages": "bcm",
        "bedrock_custom_tools": "bct",
        "bedrock_tasks": "btk",
        "bedrock_agent_memory": "bam",
    }


@pytest.mark.requisito("RF-006")
async def test_each_model_gets_its_prefixed_id(pg_db):
    from models import (BedrockAgentMemory, BedrockConversation, BedrockConversationMessage,
                        BedrockCustomTool, BedrockTask)

    async with pg_db() as s:
        conv = BedrockConversation(user_id="usr-1", session_id="s-1")
        task = BedrockTask(user_id="usr-1", title="t")
        tool = BedrockCustomTool(name="n", url="http://x")
        mem = BedrockAgentMemory(user_id="usr-1", kind="note", text="hola", source="harness")
        s.add_all([conv, task, tool, mem])
        await s.flush()
        msg = BedrockConversationMessage(conversation_id=conv.id, role="user", content="hi")
        s.add(msg)
        await s.flush()
        assert re.fullmatch(r"bco-\d+", conv.id)
        assert re.fullmatch(r"btk-\d+", task.id)
        assert re.fullmatch(r"bct-\d+", tool.id)
        assert re.fullmatch(r"bam-\d+", mem.id)
        assert re.fullmatch(r"bcm-\d+", msg.id)


@pytest.mark.requisito("RF-006")
async def test_ids_increment_per_table(pg_db):
    from models import BedrockConversation

    async with pg_db() as s:
        a = BedrockConversation(user_id="usr-1", session_id="s-a")
        b = BedrockConversation(user_id="usr-1", session_id="s-b")
        s.add_all([a, b])
        await s.flush()
        na, nb = (int(x.id.split("-")[1]) for x in (a, b))
        assert nb == na + 1


@pytest.mark.requisito("RF-006")
async def test_explicit_id_is_kept(pg_db):
    from models import BedrockTask

    async with pg_db() as s:
        t = BedrockTask(id="btk-77", user_id="usr-1", title="copiada")
        s.add(t)
        await s.flush()
        assert t.id == "btk-77"


@pytest.mark.requisito("RF-006")
async def test_no_collision_after_setval(pg_db):
    """Tras copiar filas con ids conservados, setval(max) evita la colisión (hazard de secuencias)."""
    from models import BedrockTask

    async with pg_db() as s:
        s.add_all([BedrockTask(id="btk-5", user_id="u", title="a"),
                   BedrockTask(id="btk-9", user_id="u", title="b")])
        await s.flush()
        await s.execute(text("SELECT setval('btk_id_seq', 9)"))
        nuevo = BedrockTask(user_id="u", title="c")
        s.add(nuevo)
        await s.flush()
        assert nuevo.id == "btk-10"
