"""RF-022: repositorio de memoria del agente (bedrock_agent_memory) con full-text (T-080).

Necesita Postgres real (columna generada `search_vector`, GIN, `websearch_to_tsquery`): usa la
fixture `pg_db` (TEST_DATABASE_URL desechable).

Interfaz esperada de `repositories.memory_repo` (a implementar en T-081), todas `async` y con
`db: AsyncSession` como primer argumento:
  add_memory(db, user_id, kind, text, *, agent_profile_id=None, source="harness", source_ref=None) -> BedrockAgentMemory
  list_memory(db, user_id, *, agent_profile_id=None, kind=None, limit=100, offset=0) -> list[BedrockAgentMemory]
  delete_memory(db, user_id, memory_id) -> bool
  search_memory(db, user_id, query, *, agent_profile_id=None, limit=10) -> list[tuple[BedrockAgentMemory, float]]
Si `agent_profile_id` se pasa, devuelve las del perfil + las globales (NULL) del usuario; sin él, todas
las del usuario. Usan `settings.MEMORY_FTS_CONFIG`.
"""
import re

import pytest
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.requisito("RF-022")


async def test_inserta_nota_hecho_y_manual_con_id_prefijado(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        n = await repo.add_memory(s, "usr-1", "note", "Nota sobre la entrevista", agent_profile_id="agent_support")
        f = await repo.add_memory(s, "usr-1", "fact", "Vive en Guadalajara")
        m = await repo.add_memory(s, "usr-1", "manual", "Preferencia manual")
        for row in (n, f, m):
            assert re.fullmatch(r"bam-\d+", row.id)
            assert row.source == "harness"
            assert row.source_ref is None
        assert (n.kind, f.kind, m.kind) == ("note", "fact", "manual")
        assert n.agent_profile_id == "agent_support"
        assert f.agent_profile_id is None


async def test_listar_por_usuario_y_por_perfil(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        await repo.add_memory(s, "usr-1", "note", "global", )
        await repo.add_memory(s, "usr-1", "fact", "del perfil A", agent_profile_id="A")
        await repo.add_memory(s, "usr-1", "fact", "del perfil B", agent_profile_id="B")
        await repo.add_memory(s, "usr-2", "note", "ajena")

        todas = await repo.list_memory(s, "usr-1")
        assert {r.text for r in todas} == {"global", "del perfil A", "del perfil B"}
        con_a = await repo.list_memory(s, "usr-1", agent_profile_id="A")
        assert {r.text for r in con_a} == {"global", "del perfil A"}
        hechos = await repo.list_memory(s, "usr-1", kind="fact")
        assert {r.text for r in hechos} == {"del perfil A", "del perfil B"}
        assert len(await repo.list_memory(s, "usr-1", limit=2)) == 2


async def test_borrar_solo_la_propia(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        propia = await repo.add_memory(s, "usr-1", "note", "mía")
        ajena = await repo.add_memory(s, "usr-2", "note", "tuya")
        assert await repo.delete_memory(s, "usr-1", ajena.id) is False
        assert await repo.delete_memory(s, "usr-1", propia.id) is True
        assert await repo.delete_memory(s, "usr-1", propia.id) is False
        assert [r.text for r in await repo.list_memory(s, "usr-2")] == ["tuya"]
        assert await repo.list_memory(s, "usr-1") == []


async def test_busqueda_fts_con_acentos_y_plurales_en_espanol(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        await repo.add_memory(s, "usr-1", "fact", "Prefiere trabajar en empresas de tecnología")
        await repo.add_memory(s, "usr-1", "fact", "Tiene experiencia con bases de datos relacionales")
        await repo.add_memory(s, "usr-1", "note", "Le gusta el café por las mañanas")

        # plural en la consulta, singular en el texto (stemming spanish_unaccent)
        r = await repo.search_memory(s, "usr-1", "empresa")
        assert [row.text for row, _ in r] == ["Prefiere trabajar en empresas de tecnología"]
        # acentos (D-29): `spanish_unaccent` quita tildes antes del stemmer; con `spanish` a secas
        # "tecnologias" y "tecnología" no casan
        r = await repo.search_memory(s, "usr-1", "tecnologias")
        assert len(r) == 1 and "tecnología" in r[0][0].text
        # plural/singular inverso
        r = await repo.search_memory(s, "usr-1", "base de dato")
        assert len(r) == 1 and "bases de datos" in r[0][0].text
        # sin coincidencias
        assert await repo.search_memory(s, "usr-1", "astronauta") == []


async def test_busqueda_ordena_por_ts_rank(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        poco = await repo.add_memory(s, "usr-1", "note", "python " + "relleno " * 40)
        mucho = await repo.add_memory(s, "usr-1", "note", "python python python")
        r = await repo.search_memory(s, "usr-1", "python")
        assert [row.id for row, _ in r] == [mucho.id, poco.id]
        assert r[0][1] >= r[1][1] > 0
        assert len(await repo.search_memory(s, "usr-1", "python", limit=1)) == 1


async def test_busqueda_aislada_por_usuario_y_filtra_perfil(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        await repo.add_memory(s, "usr-1", "fact", "le interesa kubernetes")
        await repo.add_memory(s, "usr-2", "fact", "le interesa kubernetes también")
        assert [row.user_id for row, _ in await repo.search_memory(s, "usr-1", "kubernetes")] == ["usr-1"]

        await repo.add_memory(s, "usr-1", "fact", "kubernetes en A", agent_profile_id="A")
        await repo.add_memory(s, "usr-1", "fact", "kubernetes en B", agent_profile_id="B")
        textos = {row.text for row, _ in await repo.search_memory(s, "usr-1", "kubernetes", agent_profile_id="A")}
        assert textos == {"le interesa kubernetes", "kubernetes en A"}


async def test_consulta_websearch_no_rompe_con_sintaxis_arbitraria(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        await repo.add_memory(s, "usr-1", "note", "algo de postgres")
        assert await repo.search_memory(s, "usr-1", '"') == []
        assert await repo.search_memory(s, "usr-1", "   ") == []
        assert len(await repo.search_memory(s, "usr-1", "postgres -oracle")) == 1


async def test_unicidad_user_id_source_ref(pg_db):
    from repositories import memory_repo as repo

    async with pg_db() as s:
        await repo.add_memory(s, "usr-1", "note", "a", source="qdrant_import", source_ref="pt-1")
        # mismo source_ref en otro usuario: permitido
        await repo.add_memory(s, "usr-2", "note", "b", source="qdrant_import", source_ref="pt-1")
        # source_ref NULL repetido: permitido
        await repo.add_memory(s, "usr-1", "note", "c")
        await repo.add_memory(s, "usr-1", "note", "d")
        with pytest.raises(IntegrityError):
            await repo.add_memory(s, "usr-1", "note", "dup", source="qdrant_import", source_ref="pt-1")
