"""Invariantes del dedupe de lecturas dentro del turno (agent_loop)."""
from services import tools
from services.agent_loop import _DEDUP_READ_TOOLS


def test_dedup_tools_are_never_write_tools():
    # El dedupe cachea el resultado durante el turno; si una de estas tools
    # fuese de escritura, se serviría un resultado obsoleto.
    for name in _DEDUP_READ_TOOLS:
        assert not tools.is_write_tool(name), f"{name} no puede ser read-dedupe y write a la vez"


def test_dedup_tools_exist_in_catalog():
    catalog = tools.all_tool_names()
    for name in _DEDUP_READ_TOOLS:
        assert name in catalog, f"{name} ya no existe en el catálogo de tools"


def test_write_tools_detected():
    # La invalidación de seen_reads tras un write depende de is_write_tool.
    assert tools.is_write_tool("update_career_record")
    assert tools.is_write_tool("create_career_record")
    assert tools.is_write_tool("delete_career_record")
    assert not tools.is_write_tool("get_career_record")
