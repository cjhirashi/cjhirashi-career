"""RF-006: repositorio de conversaciones y mensajes (bedrock_conversations / _messages) (T-060)."""
import re

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.requisito("RF-006")


def test_titulo_se_deriva_del_primer_mensaje():
    from repositories.conversation_repo import conversation_title_from

    assert conversation_title_from("  hola   mundo \n") == "hola mundo"
    assert conversation_title_from("") == "Nueva conversación"
    largo = "x" * 80
    assert conversation_title_from(largo) == "x" * 60 + "…"


async def test_get_or_create_crea_con_ids_prefijados(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(
            s, "usr-1", "sess-1", "primer mensaje", session_type="general", agent_profile_id="agent_orchestrator"
        )
        assert re.fullmatch(r"bco-\d+", conv.id)
        assert conv.title == "primer mensaje"
        assert conv.session_type == "general"
        assert conv.agent_profile_id == "agent_orchestrator"


async def test_get_or_create_es_idempotente_y_completa_el_perfil(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        a = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        assert a.agent_profile_id is None
        b = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "otro", agent_profile_id="agent_support")
        assert b.id == a.id
        assert b.agent_profile_id == "agent_support"
        # un perfil ya fijado no se pisa
        c = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "x", agent_profile_id="agent_cv_writing")
        assert c.agent_profile_id == "agent_support"
        total = (await s.execute(select(func.count()).select_from(type(a)))).scalar_one()
        assert total == 1


async def test_append_y_carga_de_historial_converse_con_ventana(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        for i in range(5):
            await repo.append_message(s, conv.id, "user" if i % 2 == 0 else "assistant", f"m{i}")
        await repo.append_message(s, conv.id, "user", "")
        out = await repo.load_converse_messages(s, "usr-1", "sess-1", window=3)
        assert [m["role"] for m in out] == ["assistant", "user", "user"]
        assert out[-1] == {"role": "user", "content": [{"text": "(sin texto)"}]}
        todo = await repo.load_converse_messages(s, "usr-1", "sess-1", window=0)
        assert len(todo) == 6
        assert todo[0] == {"role": "user", "content": [{"text": "m0"}]}


async def test_historial_de_sesion_ajena_o_inexistente_es_vacio(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        await repo.append_message(s, conv.id, "user", "secreto")
        assert await repo.load_converse_messages(s, "usr-2", "sess-1", window=20) == []
        assert await repo.load_converse_messages(s, "usr-1", "nope", window=20) == []


async def test_respuesta_del_asistente_se_sanea_al_cargar(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        await repo.append_message(s, conv.id, "assistant", "<thinking>interno</thinking>visible")
        out = await repo.load_converse_messages(s, "usr-1", "sess-1", window=20)
        assert "interno" not in out[0]["content"][0]["text"]
        assert "visible" in out[0]["content"][0]["text"]


async def test_listado_por_usuario_con_filtros_y_orden(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        await repo.get_or_create_conversation(s, "usr-1", "s-a", "a", session_type="contextual", agent_profile_id="p1")
        await repo.get_or_create_conversation(s, "usr-1", "s-b", "b", session_type="general", agent_profile_id="p2")
        await repo.get_or_create_conversation(s, "usr-2", "s-c", "c")
        todas = await repo.list_conversations(s, "usr-1")
        assert {c.session_id for c in todas} == {"s-a", "s-b"}
        assert [c.session_id for c in await repo.list_conversations(s, "usr-1", session_type="general")] == ["s-b"]
        assert [c.session_id for c in await repo.list_conversations(s, "usr-1", agent_profile_id="p1")] == ["s-a"]


async def test_mensajes_de_conversacion_en_orden_y_aislados(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        await repo.append_message(s, conv.id, "user", "uno")
        await repo.append_message(s, conv.id, "assistant", "dos")
        msgs = await repo.get_conversation_messages(s, "usr-1", "sess-1")
        assert [m.content for m in msgs] == ["uno", "dos"]
        assert all(re.fullmatch(r"bcm-\d+", m.id) for m in msgs)
        assert await repo.get_conversation_messages(s, "usr-2", "sess-1") == []


async def test_renombrar_trunca_a_255_y_respeta_propietario(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        assert await repo.rename_conversation(s, "usr-1", "sess-1", "y" * 300) is True
        conv = (await repo.list_conversations(s, "usr-1"))[0]
        assert conv.title == "y" * 255
        assert await repo.rename_conversation(s, "usr-2", "sess-1", "robo") is False
        assert await repo.rename_conversation(s, "usr-1", "nope", "x") is False


async def test_borrar_conversacion_elimina_mensajes_en_cascada(pg_db):
    from models import BedrockConversationMessage
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        conv = await repo.get_or_create_conversation(s, "usr-1", "sess-1", "hola")
        await repo.append_message(s, conv.id, "user", "uno")
        assert await repo.delete_conversation(s, "usr-2", "sess-1") is False
        assert await repo.delete_conversation(s, "usr-1", "sess-1") is True
        assert await repo.delete_conversation(s, "usr-1", "sess-1") is False
        restantes = (await s.execute(select(func.count()).select_from(BedrockConversationMessage))).scalar_one()
        assert restantes == 0


async def test_conversation_counts_by_profile_agrupa_y_aisla_por_usuario(pg_db):
    from repositories import conversation_repo as repo

    async with pg_db() as s:
        await repo.get_or_create_conversation(s, "usr-1", "s1", "a", agent_profile_id="agent_support")
        await repo.get_or_create_conversation(s, "usr-1", "s2", "b", agent_profile_id="agent_support")
        await repo.get_or_create_conversation(s, "usr-1", "s3", "c", agent_profile_id="agent_orchestrator")
        await repo.get_or_create_conversation(s, "usr-1", "s4", "d")  # sin perfil: no cuenta
        await repo.get_or_create_conversation(s, "usr-2", "s5", "e", agent_profile_id="agent_support")
        assert await repo.conversation_counts_by_profile(s, "usr-1") == {
            "agent_support": 2,
            "agent_orchestrator": 1,
        }
        assert await repo.conversation_counts_by_profile(s, "usr-9") == {}
