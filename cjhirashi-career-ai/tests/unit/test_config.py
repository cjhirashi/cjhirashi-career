"""RF-006: configuración obligatoria del harness (T-010)."""
import pytest
from pydantic import ValidationError

REQUIRED = {
    "AI_DATABASE_URL": "postgresql+asyncpg://u:p@localhost/career_ai_db",
    "SECRET_KEY": "x" * 32,
    "ALGORITHM": "HS256",
    "API_BASE_URL": "http://cjhirashi-career-api:8000",
    "AI_SERVICE_TOKEN": "service-token",
}


@pytest.fixture
def clean_env(monkeypatch):
    for name in [*REQUIRED, "MEMORY_FTS_CONFIG"]:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def _settings(**kw):
    from config import Settings

    return Settings(_env_file=None, **kw)


@pytest.mark.requisito("RF-006")
def test_settings_loads_with_all_required_vars(clean_env):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    s = _settings()
    assert s.AI_DATABASE_URL == REQUIRED["AI_DATABASE_URL"]
    assert s.API_BASE_URL == REQUIRED["API_BASE_URL"]
    assert s.AI_SERVICE_TOKEN == "service-token"
    assert s.ALGORITHM == "HS256"


@pytest.mark.requisito("RF-006")
def test_memory_fts_config_defaults_to_spanish(clean_env):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    assert _settings().MEMORY_FTS_CONFIG == "spanish"


@pytest.mark.requisito("RF-006")
def test_memory_fts_config_is_overridable(clean_env):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    clean_env.setenv("MEMORY_FTS_CONFIG", "english")
    assert _settings().MEMORY_FTS_CONFIG == "english"


@pytest.mark.requisito("RF-006")
@pytest.mark.parametrize("missing", sorted(REQUIRED))
def test_missing_required_var_fails_naming_it(clean_env, missing):
    for k, v in REQUIRED.items():
        if k != missing:
            clean_env.setenv(k, v)
    with pytest.raises(ValidationError) as exc:
        _settings()
    assert missing in str(exc.value)


@pytest.mark.requisito("RF-006")
def test_short_secret_key_is_rejected(clean_env):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    clean_env.setenv("SECRET_KEY", "corta")
    with pytest.raises(ValidationError) as exc:
        _settings()
    assert "SECRET_KEY" in str(exc.value)


@pytest.mark.requisito("RF-006")
@pytest.mark.parametrize("bad", ["spanish'); drop", "Spanish", "es-ES", "", "english simple"])
def test_invalid_fts_config_is_rejected(clean_env, bad):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    clean_env.setenv("MEMORY_FTS_CONFIG", bad)
    with pytest.raises(ValidationError) as exc:
        _settings()
    assert "MEMORY_FTS_CONFIG" in str(exc.value)


@pytest.mark.requisito("RF-003")
def test_rest_client_settings_have_safe_defaults(clean_env):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    s = _settings()
    assert s.API_TIMEOUT_SECONDS == 15.0
    assert s.API_LIST_MAX_ITEMS == 500


@pytest.mark.requisito("RF-003")
@pytest.mark.parametrize("name,value", [("API_TIMEOUT_SECONDS", "0"), ("API_LIST_MAX_ITEMS", "0")])
def test_rest_client_settings_reject_non_positive(clean_env, name, value):
    for k, v in REQUIRED.items():
        clean_env.setenv(k, v)
    clean_env.setenv(name, value)
    with pytest.raises(ValidationError):
        _settings()
