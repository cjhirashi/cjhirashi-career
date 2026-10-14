"""RF-006: repos de ajustes, perfiles (prompt, foto, tools, delegación) y tools personalizadas (T-062)."""
import re

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.requisito("RF-006")


# --------------------------------------------------------------------------- settings_repo

async def test_settings_sin_fila_devuelve_none(pg_db):
    from repositories import settings_repo

    async with pg_db() as s:
        assert await settings_repo.get_settings(s) is None
        assert await settings_repo.get_system_prompt_override(s) is None
        assert await settings_repo.get_global_rules_override(s) is None


async def test_system_prompt_y_reglas_se_fijan_y_se_limpian(pg_db):
    from models import BedrockSettings
    from repositories import settings_repo

    async with pg_db() as s:
        assert await settings_repo.set_system_prompt(s, "mi prompt") == "mi prompt"
        assert await settings_repo.set_global_rules(s, "mis reglas") == "mis reglas"
        assert await settings_repo.get_system_prompt_override(s) == "mi prompt"
        assert await settings_repo.get_global_rules_override(s) == "mis reglas"
        # una sola fila (tabla de operador único)
        assert (await s.execute(select(func.count()).select_from(BedrockSettings))).scalar_one() == 1
        assert await settings_repo.set_system_prompt(s, None) is None
        assert await settings_repo.get_system_prompt_override(s) is None
        assert await settings_repo.get_global_rules_override(s) == "mis reglas"


async def test_modelo_activo_y_orquestador(pg_db):
    from repositories import settings_repo

    async with pg_db() as s:
        await settings_repo.set_active_model_id(s, "model-a")
        await settings_repo.set_active_model_id(s, "model-b")
        row = await settings_repo.get_settings(s)
        assert row.active_model_id == "model-b"
        await settings_repo.update_settings(s, orchestrator_model_id="model-o")
        assert (await settings_repo.get_settings(s)).orchestrator_model_id == "model-o"


async def test_limites_y_presupuesto(pg_db):
    from repositories import settings_repo

    async with pg_db() as s:
        row = await settings_repo.update_settings(
            s, max_round_trips=9, history_window=40, daily_budget_usd=12.5
        )
        assert (row.max_round_trips, row.history_window, float(row.daily_budget_usd)) == (9, 40, 12.5)
        row = await settings_repo.update_settings(s, daily_budget_usd=1)
        assert row.max_round_trips == 9
        assert float(row.daily_budget_usd) == 1.0


async def test_update_settings_rechaza_campos_desconocidos(pg_db):
    from repositories import settings_repo

    async with pg_db() as s:
        with pytest.raises(ValueError, match="id"):
            await settings_repo.update_settings(s, id=7)


# --------------------------------------------------------------------------- profile_repo: prompts

async def test_prompt_suffix_override_crud(pg_db):
    from repositories import profile_repo

    async with pg_db() as s:
        assert await profile_repo.get_prompt_suffix(s, "agent_support") is None
        await profile_repo.set_prompt_suffix(s, "agent_support", "  sufijo  ")
        assert await profile_repo.get_prompt_suffix(s, "agent_support") == "sufijo"
        await profile_repo.set_prompt_suffix(s, "agent_support", "otro")
        await profile_repo.set_prompt_suffix(s, "agent_cv_writing", "cv")
        assert await profile_repo.list_prompt_overrides(s) == {"agent_support": "otro", "agent_cv_writing": "cv"}
        await profile_repo.set_prompt_suffix(s, "agent_support", "   ")
        assert await profile_repo.get_prompt_suffix(s, "agent_support") is None
        await profile_repo.set_prompt_suffix(s, "agent_cv_writing", None)
        assert await profile_repo.list_prompt_overrides(s) == {}
        await profile_repo.set_prompt_suffix(s, "agent_nunca", None)  # borrar lo inexistente no falla


# --------------------------------------------------------------------------- profile_repo: fotos

async def test_fotos_crud(pg_db):
    from repositories import profile_repo

    async with pg_db() as s:
        assert await profile_repo.photos_map(s) == {}
        assert await profile_repo.set_photo(s, "agent_support", " http://x/a.png ") == "http://x/a.png"
        assert await profile_repo.set_photo(s, "agent_support", "http://x/b.png") == "http://x/b.png"
        assert await profile_repo.photos_map(s) == {"agent_support": "http://x/b.png"}
        assert await profile_repo.set_photo(s, "agent_support", "") is None
        assert await profile_repo.photos_map(s) == {}
        assert await profile_repo.set_photo(s, "agent_support", None) is None


# --------------------------------------------------------------------------- profile_repo: tools

async def test_tool_override_distingue_none_y_lista_vacia(pg_db):
    from repositories import profile_repo

    async with pg_db() as s:
        assert await profile_repo.get_tool_override(s, "agent_github") is None
        await profile_repo.set_tool_override(s, "agent_github", ["b", "a"])
        assert await profile_repo.get_tool_override(s, "agent_github") == ["b", "a"]
        await profile_repo.set_tool_override(s, "agent_changelog", [])
        assert await profile_repo.get_tool_override(s, "agent_changelog") == []
        assert await profile_repo.list_tool_overrides(s) == {"agent_github": ["b", "a"], "agent_changelog": []}
        await profile_repo.set_tool_override(s, "agent_github", None)
        assert await profile_repo.get_tool_override(s, "agent_github") is None
        assert await profile_repo.list_tool_overrides(s) == {"agent_changelog": []}


# --------------------------------------------------------------------------- profile_repo: delegación

async def test_delegacion_override_presente_aunque_vacio(pg_db):
    from repositories import profile_repo

    async with pg_db() as s:
        assert await profile_repo.list_delegation_overrides(s) == {}
        assert await profile_repo.get_delegation_override(s, "agent_orchestrator") is None
        await profile_repo.set_delegation_override(s, "agent_orchestrator", ["agent_support"])
        await profile_repo.set_delegation_override(s, "agent_support", [])
        assert await profile_repo.get_delegation_override(s, "agent_orchestrator") == ["agent_support"]
        assert await profile_repo.list_delegation_overrides(s) == {
            "agent_orchestrator": ["agent_support"],
            "agent_support": [],
        }
        await profile_repo.set_delegation_override(s, "agent_orchestrator", ["agent_support", "agent_cv_writing"])
        assert await profile_repo.get_delegation_override(s, "agent_orchestrator") == ["agent_support", "agent_cv_writing"]
        await profile_repo.set_delegation_override(s, "agent_orchestrator", None)
        assert await profile_repo.get_delegation_override(s, "agent_orchestrator") is None


# --------------------------------------------------------------------------- custom_tool_repo

async def test_custom_tools_crud_con_id_prefijado(pg_db):
    from repositories import custom_tool_repo

    async with pg_db() as s:
        a = await custom_tool_repo.create_custom_tool(s, "mcp-a", "http://a", {"X-Key": "1"})
        b = await custom_tool_repo.create_custom_tool(s, "mcp-b", "http://b")
        assert re.fullmatch(r"bct-\d+", a.id)
        assert a.is_enabled is True
        assert a.headers == {"X-Key": "1"}
        assert b.headers is None
        assert [t.name for t in await custom_tool_repo.list_custom_tools(s)] == ["mcp-b", "mcp-a"]
        assert (await custom_tool_repo.get_custom_tool(s, a.id)).name == "mcp-a"
        assert await custom_tool_repo.get_custom_tool(s, "bct-999") is None


async def test_custom_tool_habilitar_y_borrar(pg_db):
    from repositories import custom_tool_repo

    async with pg_db() as s:
        a = await custom_tool_repo.create_custom_tool(s, "mcp-a", "http://a")
        off = await custom_tool_repo.set_custom_tool_enabled(s, a.id, False)
        assert off.is_enabled is False
        assert await custom_tool_repo.set_custom_tool_enabled(s, "bct-999", True) is None
        assert await custom_tool_repo.delete_custom_tool(s, a.id) is True
        assert await custom_tool_repo.delete_custom_tool(s, a.id) is False
        assert await custom_tool_repo.list_custom_tools(s) == []


async def test_delegacion_guarda_filter_level_allowed_como_la_api(pg_db):
    """D-13: se persiste solo lo permitido por nivel, sin duplicados ni ids desconocidos."""
    from repositories import profile_repo

    async with pg_db() as s:
        # L1 -> puede delegar a L2/L3; no a si mismo ni a desconocidos; duplicados fuera
        await profile_repo.set_delegation_override(
            s, "agent_orchestrator",
            ["agent_support", "agent_support", "nope", "agent_orchestrator", "agent_changelog"],
        )
        assert await profile_repo.get_delegation_override(s, "agent_orchestrator") == [
            "agent_support", "agent_changelog",
        ]
        # L3 no delega: todo se descarta, pero el override (vacio) sigue presente
        await profile_repo.set_delegation_override(s, "agent_changelog", ["agent_support"])
        assert await profile_repo.get_delegation_override(s, "agent_changelog") == []
        # L2 no delega hacia arriba ni al mismo nivel
        await profile_repo.set_delegation_override(s, "agent_support", ["agent_orchestrator", "agent_networking", "agent_changelog"])
        assert await profile_repo.get_delegation_override(s, "agent_support") == ["agent_changelog"]
        with pytest.raises(KeyError):
            await profile_repo.set_delegation_override(s, "agent_inexistente", ["agent_support"])
