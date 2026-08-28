"""Anti-drift: el mapa estático de la migración b2c3d4e5f6a7 debe seguir cuadrando
con el registro de secciones en código (ADR-021)."""
import importlib.util
from pathlib import Path

from services.admin_sections import list_section_specs

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "b2c3d4e5f6a7_admin_section_overrides_synthetic_pk.py"
)


def _load_slug_to_pk() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("_mig_b2c3d4e5f6a7", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._SLUG_TO_PK


def test_migration_map_matches_code_registry_exactly():
    mig = _load_slug_to_pk()
    code = {spec.system_name: spec.id for spec in list_section_specs()}

    missing = set(code) - set(mig)
    extra = set(mig) - set(code)
    mismatched = {k: (code[k], mig[k]) for k in code if k in mig and code[k] != mig[k]}

    assert not missing, f"slugs en código pero no en la migración: {sorted(missing)}"
    assert not extra, f"slugs en la migración pero no en código: {sorted(extra)}"
    assert not mismatched, f"sec-N distinto entre código y migración: {mismatched}"
    assert mig == code


def test_migration_map_is_contiguous_sec_1_to_54():
    nums = sorted(int(v.split("-")[1]) for v in _load_slug_to_pk().values())
    assert nums == list(range(1, 55))
