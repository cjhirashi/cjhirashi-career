"""RF-006: repositorio de tareas (bedrock_tasks) con subtareas, filtros, orden, conteo y distinct (T-066)."""
import re

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.requisito("RF-006")

U = "usr-1"


async def _mk(s, title, user=U, **extra):
    from repositories import task_repo

    return await task_repo.create_for_user(s, user, {"title": title, **extra})


async def test_crear_asigna_id_prefijado_y_fuerza_user_id(pg_db):
    async with pg_db() as s:
        t = await _mk(s, "Tarea", user_id="usr-intruso")
        assert re.fullmatch(r"btk-\d+", t.id)
        assert t.user_id == U
        assert (t.status, t.priority, t.assignee_type, t.is_blocking) == ("pending", "medium", "user", True)


async def test_get_update_delete_estan_acotados_al_usuario(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        t = await _mk(s, "Tarea")
        assert (await task_repo.get_for_user(s, U, t.id)).title == "Tarea"
        assert await task_repo.get_for_user(s, "usr-2", t.id) is None
        assert await task_repo.update_for_user(s, "usr-2", t.id, {"title": "robo"}) is None
        upd = await task_repo.update_for_user(s, U, t.id, {"title": "Nueva", "status": "done", "user_id": "x"})
        assert (upd.title, upd.status, upd.user_id) == ("Nueva", "done", U)
        assert await task_repo.delete_for_user(s, "usr-2", t.id) is False
        assert await task_repo.delete_for_user(s, U, t.id) is True
        assert await task_repo.get_for_user(s, U, t.id) is None


async def test_listado_ordena_por_id_desc_por_defecto_y_por_columna_valida(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        a = await _mk(s, "b-tarea", priority="low")
        b = await _mk(s, "a-tarea", priority="high")
        await _mk(s, "otra", user="usr-2")
        por_defecto = await task_repo.list_for_user(s, U)
        assert [t.id for t in por_defecto] == [b.id, a.id]
        asc = await task_repo.list_for_user(s, U, sort_by="title", sort_dir="asc")
        assert [t.title for t in asc] == ["a-tarea", "b-tarea"]
        desc = await task_repo.list_for_user(s, U, sort_by="title", sort_dir="desc")
        assert [t.title for t in desc] == ["b-tarea", "a-tarea"]
        # columna inexistente o inyección: se ignora y se usa el orden por defecto
        raro = await task_repo.list_for_user(s, U, sort_by="title; DROP TABLE x")
        assert [t.id for t in raro] == [b.id, a.id]


async def test_paginacion_con_skip_y_limit(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        for i in range(5):
            await _mk(s, f"t{i}")
        pagina = await task_repo.list_for_user(s, U, skip=1, limit=2, sort_by="title")
        assert [t.title for t in pagina] == ["t1", "t2"]
        assert await task_repo.count_for_user(s, U) == 5


async def test_busqueda_ilike_sobre_columnas_de_texto(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        await _mk(s, "Revisar CV", description="para Acme")
        await _mk(s, "Otra", notes="mira el CV viejo")
        await _mk(s, "Nada")
        assert {t.title for t in await task_repo.list_for_user(s, U, search="cv")} == {"Revisar CV", "Otra"}
        assert await task_repo.count_for_user(s, U, search="acme") == 1
        assert await task_repo.count_for_user(s, U, search="zzz") == 0


async def test_filtros_igualdad_lista_booleano_y_claves_desconocidas(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        await _mk(s, "a", status="pending", priority="high", is_blocking=True)
        await _mk(s, "b", status="done", priority="low", is_blocking=False)
        await _mk(s, "c", status="in_progress", priority="low", is_blocking=True)

        def titulos(rows):
            return sorted(t.title for t in rows)

        assert titulos(await task_repo.list_for_user(s, U, filters={"status": "done"})) == ["b"]
        assert titulos(await task_repo.list_for_user(s, U, filters={"status": ["done", "pending"]})) == ["a", "b"]
        assert titulos(await task_repo.list_for_user(s, U, filters={"priority": "low", "status": "in_progress"})) == ["c"]
        assert titulos(await task_repo.list_for_user(s, U, filters={"is_blocking": "false"})) == ["b"]
        assert titulos(await task_repo.list_for_user(s, U, filters={"is_blocking": ["si", "no"]})) == ["a", "b", "c"]
        # clave desconocida, id/user_id y valores vacíos se ignoran
        assert len(await task_repo.list_for_user(s, U, filters={"nope": "x", "user_id": "usr-2", "status": ""})) == 3
        assert await task_repo.count_for_user(s, U, filters={"status": ["done", "pending"]}) == 2


async def test_valores_distintos_de_una_columna_de_texto(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        await _mk(s, "a", agent_profile_id="agent_support", assignee_type="agent")
        await _mk(s, "b", agent_profile_id="agent_support", assignee_type="agent")
        await _mk(s, "c", agent_profile_id="agent_cv_writing", assignee_type="agent")
        await _mk(s, "d", agent_profile_id="", assignee_type="user")
        await _mk(s, "e", agent_profile_id="agent_otro", user="usr-2")
        assert await task_repo.distinct_values_for_user(s, U, "agent_profile_id") == [
            "agent_cv_writing", "agent_support"]
        assert task_repo.is_distinct_field("agent_profile_id") is True
        assert task_repo.is_distinct_field("id") is False
        assert task_repo.is_distinct_field("user_id") is False
        assert task_repo.is_distinct_field("sort_order") is False
        with pytest.raises(ValueError, match="not a text column"):
            await task_repo.distinct_values_for_user(s, U, "sort_order")


async def test_padre_valido_y_reglas_de_jerarquia(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await _mk(s, "padre")
        hija = await _mk(s, "hija", parent_id=padre.id)
        assert hija.parent_id == padre.id
        with pytest.raises(ValueError, match="no existe o no es tuyo"):
            await _mk(s, "x", parent_id="btk-9999")
        with pytest.raises(ValueError, match="no existe o no es tuyo"):
            await _mk(s, "x", user="usr-2", parent_id=padre.id)
        with pytest.raises(ValueError, match="no pueden tener subtareas"):
            await _mk(s, "nieta", parent_id=hija.id)
        with pytest.raises(ValueError, match="padre de sí misma"):
            await task_repo.update_for_user(s, U, padre.id, {"parent_id": padre.id})
        with pytest.raises(ValueError, match="no pueden tener subtareas"):
            await task_repo.update_for_user(s, U, padre.id, {"parent_id": hija.id})


async def test_subtareas_anidadas_se_crean_con_sort_order(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(
            s, U, {"title": "plan", "subtasks": [{"title": "paso 1"}, {"title": "paso 2", "is_blocking": False}]}
        )
        hijas = await task_repo.list_children(s, U, padre.id)
        assert [(h.title, h.sort_order, h.parent_id) for h in hijas] == [("paso 1", 0, padre.id), ("paso 2", 1, padre.id)]
        assert hijas[1].is_blocking is False
        assert all(re.fullmatch(r"btk-\d+", h.id) for h in hijas)


async def test_sincronizar_subtareas_actualiza_crea_y_borra(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(
            s, U, {"title": "plan", "subtasks": [{"title": "uno"}, {"title": "dos"}, {"title": "tres"}]}
        )
        uno, dos, _tres = await task_repo.list_children(s, U, padre.id)
        await task_repo.update_for_user(
            s, U, padre.id,
            {"subtasks": [{"title": "dos-bis", "id": dos.id}, {"title": "cuatro"}, {"title": "uno-bis", "id": uno.id}]},
        )
        hijas = await task_repo.list_children(s, U, padre.id)
        assert [(h.title, h.sort_order) for h in hijas] == [("dos-bis", 0), ("cuatro", 1), ("uno-bis", 2)]
        assert {h.id for h in hijas} >= {uno.id, dos.id}
        # `subtasks=[]` borra todas las hijas; ausente no las toca
        await task_repo.update_for_user(s, U, padre.id, {"title": "plan 2"})
        assert len(await task_repo.list_children(s, U, padre.id)) == 3
        await task_repo.update_for_user(s, U, padre.id, {"subtasks": []})
        assert await task_repo.list_children(s, U, padre.id) == []


async def test_una_subtarea_no_puede_tener_subtareas(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(s, U, {"title": "plan", "subtasks": [{"title": "uno"}]})
        (hija,) = await task_repo.list_children(s, U, padre.id)
        with pytest.raises(ValueError, match="no pueden tener subtareas"):
            await task_repo.update_for_user(s, U, hija.id, {"subtasks": [{"title": "nieta"}]})


async def test_borrar_el_padre_borra_las_hijas_en_cascada(pg_db):
    from models import BedrockTask
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(s, U, {"title": "plan", "subtasks": [{"title": "a"}, {"title": "b"}]})
        otra = await _mk(s, "suelta")
        assert await task_repo.delete_for_user(s, U, padre.id) is True
        restantes = (await s.execute(select(BedrockTask.id))).scalars().all()
        assert restantes == [otra.id]
        assert (await s.execute(select(func.count()).select_from(BedrockTask))).scalar_one() == 1


# --- paridad con la API (D-13): las subtareas pasan por SubtaskInput + model_dump() ---

async def test_subtarea_omitida_vuelve_a_sus_defaults_como_en_la_api(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(
            s, U, {"title": "plan", "subtasks": [{"title": "uno", "status": "in_progress", "priority": "high", "notes": "n"}]}
        )
        [uno] = await task_repo.list_children(s, U, padre.id)
        assert (uno.status, uno.priority, uno.notes) == ("in_progress", "high", "n")
        await task_repo.update_for_user(s, U, padre.id, {"subtasks": [{"id": uno.id, "title": "uno-bis"}]})
        [uno] = await task_repo.list_children(s, U, padre.id)
        assert (uno.title, uno.status, uno.priority, uno.notes) == ("uno-bis", "pending", "medium", None)
        assert uno.is_blocking is True and uno.assignee_type == "user"


async def test_subtarea_sin_titulo_es_error_de_validacion_no_integrity_error(pg_db):
    from pydantic import ValidationError

    from repositories import task_repo

    async with pg_db() as s:
        with pytest.raises(ValidationError, match="title"):
            await task_repo.create_for_user(s, U, {"title": "plan", "subtasks": [{"description": "sin titulo"}]})
        await s.rollback()
        padre = await _mk(s, "otro")
        with pytest.raises(ValidationError, match="title"):
            await task_repo.update_for_user(s, U, padre.id, {"subtasks": [{"notes": "x"}]})


@pytest.mark.parametrize(
    "bad",
    [
        {"title": "x", "status": "nope"},
        {"title": "x", "priority": "urgente"},
        {"title": "x", "assignee_type": "robot"},
        {"title": "x", "assignee_type": "agent"},
        {"title": "x", "assignee_type": "agent", "agent_profile_id": "agent_inexistente"},
        {"title": "x", "scheduled_at": "2026-02-01T00:00:00Z", "due_at": "2026-01-01T00:00:00Z"},
    ],
)
async def test_subtarea_invalida_se_rechaza_con_validacion(pg_db, bad):
    from pydantic import ValidationError

    from repositories import task_repo

    async with pg_db() as s:
        with pytest.raises(ValidationError):
            await task_repo.create_for_user(s, U, {"title": "plan", "subtasks": [bad]})


async def test_subtarea_de_usuario_normaliza_agente_y_ejecucion(pg_db):
    from repositories import task_repo

    async with pg_db() as s:
        padre = await task_repo.create_for_user(
            s, U, {"title": "plan", "subtasks": [
                {"title": "u", "agent_profile_id": "agent_support", "execute_on_turn": True},
                {"title": "a", "assignee_type": "agent", "agent_profile_id": " agent_support ", "execute_on_turn": True},
            ]},
        )
        u, a = await task_repo.list_children(s, U, padre.id)
        assert (u.agent_profile_id, u.execute_on_turn) == (None, False)
        assert (a.agent_profile_id, a.execute_on_turn) == ("agent_support", True)
