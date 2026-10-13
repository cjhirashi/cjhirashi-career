"""Spec 007 — Vacantes: etapa del proceso y estado calculado.

Bloque A: catálogo y reglas puras de `services/vacancy_stage.py`.
Bloque B: modelo `Vacancy` y schemas (`career_search`).
El canon de los valores es `contracts/process-stage-catalog.json` de la spec.
"""
import json
from typing import get_args
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.vacancy import Vacancy
from repositories.career_repository import CareerRepository
from schemas.career_search import VacancyCreate, VacancyResponse, VacancyUpdate
from services import vacancy_stage
from services.vacancy_stage import (
    PROCESS_STAGES,
    STAGE_TO_STATUS,
    ProcessStage,
    prepare_vacancy_write,
    stages_for_statuses,
    vacancy_status_for,
)

_CONTRACT = (
    Path(__file__).resolve().parents[2].parent
    / ".harness"
    / "specs"
    / "007-vacantes-etapa-y-estado"
    / "contracts"
    / "process-stage-catalog.json"
)
CATALOG = json.loads(_CONTRACT.read_text(encoding="utf-8"))
CONTRACT_STAGES = [s["value"] for s in CATALOG["stages"]]
CONTRACT_STATUSES = [s["value"] for s in CATALOG["statuses"]]
NOW = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 10, 14, 9, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# T-001 — catálogo y mapeo
# ---------------------------------------------------------------------------

@pytest.mark.requisito("RF-004")
def test_catalog_matches_contract_values_and_order():
    assert list(PROCESS_STAGES) == CONTRACT_STAGES
    assert len(PROCESS_STAGES) == 13
    # El Literal no puede divergir de la tupla canónica.
    assert get_args(ProcessStage) == PROCESS_STAGES
    assert dict(STAGE_TO_STATUS) == {s["value"]: s["status"] for s in CATALOG["stages"]}


@pytest.mark.requisito("RF-004")
@pytest.mark.parametrize("entry", CATALOG["stages"], ids=lambda e: e["value"])
def test_vacancy_status_for_each_stage_is_never_null(entry):
    result = vacancy_status_for(entry["value"])
    assert result == entry["status"]
    assert result in CONTRACT_STATUSES


@pytest.mark.requisito("RF-017")
@pytest.mark.parametrize("status", CONTRACT_STATUSES)
def test_stages_for_statuses_single_status_matches_contract(status):
    expected = [s["value"] for s in CATALOG["stages"] if s["status"] == status]
    assert sorted(stages_for_statuses([status])) == sorted(expected)


@pytest.mark.requisito("RF-017")
def test_stages_for_statuses_two_statuses_is_the_union():
    expected = [
        s["value"] for s in CATALOG["stages"] if s["status"] in ("pending", "closed")
    ]
    assert sorted(stages_for_statuses(["pending", "closed"])) == sorted(expected)


@pytest.mark.requisito("RF-017")
def test_stages_for_statuses_only_invalid_is_empty():
    assert list(stages_for_statuses(["foo", "bar"])) == []
    assert list(stages_for_statuses([])) == []


@pytest.mark.requisito("RF-017")
def test_stages_for_statuses_ignores_unknown_among_valid():
    assert sorted(stages_for_statuses(["pending", "zzz"])) == ["not_applied"]


# ---------------------------------------------------------------------------
# T-002 — reglas de escritura (reloj inyectable)
# ---------------------------------------------------------------------------

@pytest.mark.requisito("RF-002")
def test_write_rejects_stage_outside_catalog_on_create_and_update():
    with pytest.raises(ValueError):
        prepare_vacancy_write({"process_stage": "foo"}, now=NOW)
    with pytest.raises(ValueError):
        prepare_vacancy_write({"process_stage": "foo"}, current_stage="applied", now=NOW)


@pytest.mark.requisito("RF-002")
def test_write_rejects_null_stage():
    with pytest.raises(ValueError):
        prepare_vacancy_write({"process_stage": None}, now=NOW)
    with pytest.raises(ValueError):
        prepare_vacancy_write({"process_stage": None}, current_stage="applied", now=NOW)


@pytest.mark.requisito("RF-005")
@pytest.mark.requisito("RF-023")
def test_write_strips_read_only_fields():
    data = {
        "company": "ACME",
        "process_stage": "applied",
        "vacancy_status": "closed",
        "process_stage_updated_at": "1999-01-01T00:00:00Z",
    }
    out = prepare_vacancy_write(data, current_stage="applied", now=NOW)
    assert "vacancy_status" not in out
    assert "process_stage_updated_at" not in out
    assert out["company"] == "ACME"
    # no muta la entrada
    assert "vacancy_status" in data


@pytest.mark.requisito("RF-021")
def test_create_sets_stage_timestamp_to_injected_utc_instant():
    out = prepare_vacancy_write({"company": "ACME"}, now=NOW)
    assert out["process_stage_updated_at"] == NOW
    assert out["process_stage_updated_at"].tzinfo is not None
    out = prepare_vacancy_write(
        {"company": "ACME", "process_stage": "applied", "process_stage_updated_at": "x"},
        now=NOW,
    )
    assert out["process_stage_updated_at"] == NOW


@pytest.mark.requisito("RF-021")
def test_default_clock_is_utc_aware():
    out = prepare_vacancy_write({"company": "ACME"})
    assert out["process_stage_updated_at"].utcoffset().total_seconds() == 0


@pytest.mark.requisito("RF-021")
def test_update_with_different_stage_sets_timestamp():
    out = prepare_vacancy_write(
        {"process_stage": "hr_interview"}, current_stage="applied", now=LATER
    )
    assert out["process_stage"] == "hr_interview"
    assert out["process_stage_updated_at"] == LATER


@pytest.mark.requisito("RF-022")
def test_update_with_omitted_or_same_stage_does_not_include_timestamp():
    omitted = prepare_vacancy_write({"company": "X"}, current_stage="applied", now=LATER)
    assert "process_stage_updated_at" not in omitted
    same = prepare_vacancy_write(
        {"process_stage": "applied", "company": "X"}, current_stage="applied", now=LATER
    )
    assert "process_stage_updated_at" not in same


@pytest.mark.requisito("RF-023")
def test_update_cannot_smuggle_timestamp_when_stage_unchanged():
    out = prepare_vacancy_write(
        {"process_stage_updated_at": "2000-01-01T00:00:00Z"},
        current_stage="applied",
        now=LATER,
    )
    assert "process_stage_updated_at" not in out


def test_module_exposes_read_only_fields_constant():
    assert vacancy_stage.READ_ONLY_VACANCY_FIELDS == {
        "vacancy_status",
        "process_stage_updated_at",
    }


# ---------------------------------------------------------------------------
# T-010 — modelo (SQLite in-memory sólo con la tabla `vacancies`) y schemas
# ---------------------------------------------------------------------------

@pytest.fixture
def vacancy_session():
    """Sesión síncrona sobre SQLite con sólo la tabla `vacancies` (ids explícitos:
    el listener de ids prefijados usa secuencias de Postgres)."""
    engine = create_engine("sqlite:///:memory:")
    Vacancy.__table__.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.mark.requisito("RF-003")
@pytest.mark.requisito("RF-001")
def test_model_defaults_to_not_applied_with_stage_timestamp(vacancy_session):
    vac = Vacancy(id="vac-t1", user_id="usr-1", company="ACME", exact_role="Dev")
    vacancy_session.add(vac)
    vacancy_session.flush()
    vacancy_session.refresh(vac)
    assert vac.process_stage == "not_applied"
    assert vac.process_stage_updated_at is not None


@pytest.mark.requisito("RF-006")
def test_model_column_definition_and_named_check():
    table = Vacancy.__table__
    assert "application_status" not in table.c
    col = table.c.process_stage
    assert col.nullable is False
    assert col.index is True
    assert table.c.process_stage_updated_at.nullable is False
    checks = {c.name: str(c.sqltext) for c in table.constraints if c.name}
    assert "ck_vacancies_process_stage" in checks
    for stage in PROCESS_STAGES:
        assert f"'{stage}'" in checks["ck_vacancies_process_stage"]


@pytest.mark.requisito("RF-006")
def test_db_check_rejects_stage_outside_catalog_on_insert_and_update(vacancy_session):
    vacancy_session.add(
        Vacancy(id="vac-bad", user_id="usr-1", company="A", exact_role="R", process_stage="foo")
    )
    with pytest.raises(IntegrityError):
        vacancy_session.flush()
    vacancy_session.rollback()

    vacancy_session.add(Vacancy(id="vac-ok", user_id="usr-1", company="A", exact_role="R"))
    vacancy_session.flush()
    with pytest.raises(IntegrityError):
        vacancy_session.execute(
            text("UPDATE vacancies SET process_stage = 'foo' WHERE id = 'vac-ok'")
        )
    vacancy_session.rollback()


@pytest.mark.requisito("RF-003")
def test_create_schema_without_stage_defaults_to_not_applied():
    model = VacancyCreate(company="ACME", exact_role="Dev")
    assert model.process_stage == "not_applied"


@pytest.mark.requisito("RF-002")
def test_schemas_reject_stage_outside_catalog():
    with pytest.raises(ValidationError):
        VacancyCreate(company="ACME", exact_role="Dev", process_stage="foo")
    with pytest.raises(ValidationError):
        VacancyUpdate(process_stage="foo")


@pytest.mark.requisito("RF-005")
@pytest.mark.requisito("RF-023")
def test_create_and_update_schemas_discard_read_only_fields():
    extra = {"vacancy_status": "closed", "process_stage_updated_at": "2000-01-01T00:00:00Z"}
    created = VacancyCreate(company="ACME", exact_role="Dev", **extra).model_dump()
    updated = VacancyUpdate(process_stage="applied", **extra).model_dump(exclude_unset=True)
    for dumped in (created, updated):
        assert "vacancy_status" not in dumped
        assert "process_stage_updated_at" not in dumped


@pytest.mark.requisito("RF-002")
def test_update_schema_rejects_explicit_null_stage_but_allows_omission():
    with pytest.raises(ValidationError):
        VacancyUpdate(process_stage=None)
    assert VacancyUpdate(company="X").model_dump(exclude_unset=True) == {"company": "X"}


@pytest.mark.requisito("RF-004")
def test_response_exposes_computed_vacancy_status():
    base = dict(
        id="vac-1",
        user_id="usr-1",
        company="ACME",
        exact_role="Dev",
        created_at=NOW,
        updated_at=NOW,
        process_stage_updated_at=NOW,
    )
    for entry in CATALOG["stages"]:
        dumped = VacancyResponse(**base, process_stage=entry["value"]).model_dump()
        assert dumped["vacancy_status"] == entry["status"]
        assert dumped["process_stage_updated_at"] == NOW
    assert "application_status" not in VacancyResponse.model_fields


# ---------------------------------------------------------------------------
# Bloque C — CareerRepository de `vacancies` (SQLite async con sólo la tabla
# `vacancies`; ids explícitos porque el listener usa secuencias de Postgres)
# ---------------------------------------------------------------------------

USER = "usr-1"


@pytest.fixture
async def repo_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Vacancy.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    repo = CareerRepository(Vacancy, resource_key="vacancies")

    async def _no_index(obj, user_id):  # la indexación en la KB no es objeto de estos tests
        return None

    repo._index_for_search = _no_index
    async with factory() as session:
        yield repo, session
    await engine.dispose()


async def _create(repo, session, n, **extra):
    data = {"id": f"vac-{n}", "company": f"C{n}", "exact_role": "Dev", **extra}
    return await repo.create_for_user(session, USER, data)


@pytest.mark.requisito("RF-003")
async def test_repo_create_without_stage_defaults_to_not_applied(repo_env):
    repo, session = repo_env
    vac = await _create(repo, session, 1)
    assert vac.process_stage == "not_applied"
    assert vac.process_stage_updated_at is not None


@pytest.mark.requisito("RF-002")
async def test_repo_invalid_stage_raises_value_error_and_session_stays_usable(repo_env):
    repo, session = repo_env
    with pytest.raises(ValueError):
        await _create(repo, session, 1, process_stage="foo")
    with pytest.raises(ValueError):
        await _create(repo, session, 2, process_stage=None)
    ok = await _create(repo, session, 3)  # la sesión no quedó rota
    with pytest.raises(ValueError):
        await repo.update_for_user(session, USER, ok.id, {"process_stage": "foo"})
    with pytest.raises(ValueError):
        await repo.update_for_user(session, USER, ok.id, {"process_stage": None})
    assert (await repo.get_for_user(session, USER, ok.id)).process_stage == "not_applied"


@pytest.mark.requisito("RF-005")
@pytest.mark.requisito("RF-023")
async def test_repo_ignores_read_only_fields_in_data(repo_env):
    repo, session = repo_env
    old = datetime(2000, 1, 1, tzinfo=timezone.utc)
    vac = await _create(
        repo, session, 1, vacancy_status="closed", process_stage_updated_at=old
    )
    assert vac.process_stage_updated_at.replace(tzinfo=timezone.utc) != old
    assert not hasattr(vac, "vacancy_status")
    before = vac.process_stage_updated_at
    upd = await repo.update_for_user(
        session, USER, vac.id, {"vacancy_status": "closed", "process_stage_updated_at": old}
    )
    assert upd.process_stage == "not_applied"
    assert upd.process_stage_updated_at == before


@pytest.mark.requisito("RF-022")
@pytest.mark.requisito("RF-021")
async def test_repo_update_moves_timestamp_only_when_stage_changes(repo_env):
    repo, session = repo_env
    vac = await _create(repo, session, 1, process_stage="applied")
    t0 = vac.process_stage_updated_at
    other = await repo.update_for_user(session, USER, vac.id, {"company": "Nueva"})
    assert other.company == "Nueva"
    assert other.process_stage_updated_at == t0
    same = await repo.update_for_user(session, USER, vac.id, {"process_stage": "applied"})
    assert same.process_stage_updated_at == t0
    moved = await repo.update_for_user(session, USER, vac.id, {"process_stage": "hr_interview"})
    assert moved.process_stage == "hr_interview"
    assert moved.process_stage_updated_at > t0


@pytest.fixture
async def seeded(repo_env):
    repo, session = repo_env
    for i, stage in enumerate(PROCESS_STAGES, start=1):
        await _create(repo, session, i, process_stage=stage)
    return repo, session


async def _stages(repo, session, filters):
    rows = await repo.list_for_user(session, USER, limit=100, filters=filters)
    count = await repo.count_for_user(session, USER, filters=filters)
    assert count == len(rows)
    return sorted(r.process_stage for r in rows)


def _same_instant(a: str, b: str) -> bool:
    # SQLite devuelve datetimes sin zona tras recargar; Postgres con zona.
    return a.rstrip("Z") == b.rstrip("Z")


def _expected(*statuses):
    return sorted(s["value"] for s in CATALOG["stages"] if s["status"] in statuses)


@pytest.mark.requisito("RF-017")
@pytest.mark.parametrize("status", CONTRACT_STATUSES)
async def test_filter_by_each_vacancy_status(seeded, status):
    repo, session = seeded
    assert await _stages(repo, session, {"vacancy_status": [status]}) == _expected(status)
    assert await _stages(repo, session, {"vacancy_status": status}) == _expected(status)


@pytest.mark.requisito("RF-017")
async def test_filter_by_two_statuses_and_invalid_status(seeded):
    repo, session = seeded
    got = await _stages(repo, session, {"vacancy_status": ["pending", "closed"]})
    assert got == _expected("pending", "closed")
    assert await _stages(repo, session, {"vacancy_status": ["foo"]}) == []
    assert await _stages(repo, session, {"vacancy_status": ["foo", "closed"]}) == _expected("closed")


@pytest.mark.requisito("RF-017")
async def test_vacancy_status_and_process_stage_filters_intersect(seeded):
    repo, session = seeded
    f = {"vacancy_status": ["in_process"], "process_stage": ["applied", "hired"]}
    assert await _stages(repo, session, f) == ["applied"]
    f = {"vacancy_status": ["pending"], "process_stage": ["hired"]}
    assert await _stages(repo, session, f) == []


@pytest.mark.requisito("RF-017")
async def test_column_filter_of_other_resource_is_unchanged():
    # R-6: `vacancy_status` no es columna; en otros recursos sigue ignorándose
    # como clave desconocida y los filtros por columna siguen funcionando.
    other = CareerRepository(Vacancy, resource_key="projects")
    stmt = other._apply_filters(select(Vacancy), {"vacancy_status": ["closed"]})
    assert stmt.whereclause is None
    stmt = other._apply_filters(select(Vacancy), {"process_stage": ["hired"]})
    assert "process_stage" in str(stmt.whereclause)


@pytest.mark.requisito("RF-023")
def test_kb_text_has_process_stage_but_not_timestamp_or_status():
    repo = CareerRepository(Vacancy, resource_key="vacancies")
    vac = Vacancy(
        id="vac-kb", user_id=USER, company="ACME", exact_role="Dev",
        process_stage="hr_interview", process_stage_updated_at=NOW,
    )
    text_ = repo._record_to_text(vac)
    assert "process_stage: hr_interview" in text_
    assert "process_stage_updated_at" not in text_
    assert "vacancy_status" not in text_
    assert "company: ACME" in text_


# ---------------------------------------------------------------------------
# Bloque D — ruta HTTP `/career/vacancies` y job discovery
#
# No requiere Postgres: SQLite en memoria con las tablas `users` y `vacancies`,
# `get_db` sobreescrito y un shim de `nextval` (el listener de ids prefijados
# lo usa). El JWT es real (AuthService) y pasa por `get_current_user`.
# ---------------------------------------------------------------------------

@pytest.fixture
async def http_env(monkeypatch):
    from sqlalchemy import event
    from sqlalchemy.pool import StaticPool
    from httpx import AsyncClient, ASGITransport

    import app as app_module
    from database import get_db
    from models.user import User
    from services.auth_service import AuthService

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    counter = iter(range(1, 10_000))

    @event.listens_for(engine.sync_engine, "connect")
    def _shim_nextval(dbapi_conn, _):
        dbapi_conn.create_function("nextval", 1, lambda _seq: next(counter))

    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Vacancy.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(CareerRepository, "_index_for_search", _noop)
    monkeypatch.setattr(app_module, "areport_error", _noop)

    async def _get_db():
        async with factory() as session:
            yield session
            await session.commit()

    app_module.app.dependency_overrides[get_db] = _get_db
    async with factory() as session:
        user = User(
            username="u007", email="u007@example.com", password_hash="x",
            full_name="U", is_active=True, is_verified=True,
        )
        session.add(user)
        await session.commit()
        user_id = user.id
    token, _ = AuthService.create_access_token(data={"sub": str(user_id)})
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client, factory, user_id
    app_module.app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


VAC = {"company": "ACME", "exact_role": "Dev"}


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-004")
@pytest.mark.parametrize("entry", CATALOG["stages"], ids=lambda e: e["value"])
async def test_http_post_and_put_with_each_stage(http_env, entry):
    client, _, _ = http_env
    created = await client.post("/career/vacancies", json={**VAC, "process_stage": entry["value"]})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["process_stage"] == entry["value"]
    assert body["vacancy_status"] == entry["status"]
    assert body["process_stage_updated_at"]
    other = "applied" if entry["value"] != "applied" else "screening"
    put = await client.put(f"/career/vacancies/{body['id']}", json={"process_stage": entry["value"]})
    assert put.status_code == 200
    assert put.json()["vacancy_status"] == entry["status"]
    assert _same_instant(put.json()["process_stage_updated_at"], body["process_stage_updated_at"])  # RF-022
    moved = await client.put(f"/career/vacancies/{body['id']}", json={"process_stage": other})
    assert moved.json()["process_stage"] == other


@pytest.mark.requisito("RF-003")
async def test_http_post_without_stage_is_not_applied(http_env):
    client, _, _ = http_env
    body = (await client.post("/career/vacancies", json=VAC)).json()
    assert body["process_stage"] == "not_applied"
    assert body["vacancy_status"] == "pending"


@pytest.mark.requisito("RF-002")
async def test_http_invalid_or_null_stage_is_422_and_does_not_change_data(http_env):
    client, _, _ = http_env
    assert (await client.post("/career/vacancies", json={**VAC, "process_stage": "foo"})).status_code == 422
    assert (await client.post("/career/vacancies", json={**VAC, "process_stage": None})).status_code == 422
    body = (await client.post("/career/vacancies", json={**VAC, "process_stage": "applied"})).json()
    url = f"/career/vacancies/{body['id']}"
    assert (await client.put(url, json={"process_stage": "foo"})).status_code == 422
    assert (await client.put(url, json={"process_stage": None})).status_code == 422
    after = (await client.get(url)).json()
    assert after["process_stage"] == "applied"
    assert _same_instant(after["process_stage_updated_at"], body["process_stage_updated_at"])


@pytest.mark.requisito("RF-005")
@pytest.mark.requisito("RF-023")
async def test_http_read_only_fields_are_not_persisted(http_env):
    client, _, _ = http_env
    sneaky = {"vacancy_status": "closed", "process_stage_updated_at": "2000-01-01T00:00:00Z"}
    body = (await client.post("/career/vacancies", json={**VAC, **sneaky})).json()
    assert body["vacancy_status"] == "pending"
    assert not body["process_stage_updated_at"].startswith("2000")
    put = await client.put(f"/career/vacancies/{body['id']}", json=sneaky)
    assert put.status_code == 200
    assert put.json()["vacancy_status"] == "pending"
    assert _same_instant(put.json()["process_stage_updated_at"], body["process_stage_updated_at"])


@pytest.mark.requisito("RF-017")
async def test_http_list_and_count_filter_by_vacancy_status(http_env):
    import json as _json

    client, _, _ = http_env
    for stage in PROCESS_STAGES:
        assert (await client.post("/career/vacancies", json={**VAC, "process_stage": stage})).status_code == 201
    for statuses in (["pending"], ["in_process"], ["closed"], ["pending", "closed"], ["foo"]):
        params = {"filters": _json.dumps({"vacancy_status": statuses}), "limit": 100}
        rows = (await client.get("/career/vacancies", params=params)).json()
        count = (await client.get("/career/vacancies/count", params={"filters": params["filters"]})).json()
        expected = _expected(*statuses)
        assert sorted(r["process_stage"] for r in rows) == expected
        assert count["count"] == len(expected)


@pytest.mark.requisito("RF-003")
async def test_job_discovery_saved_vacancy_is_not_applied_with_stage_date(http_env):
    from services.job_discovery.service import save_listings

    _, factory, user_id = http_env
    async with factory() as session:
        result = await save_listings(
            session,
            user_id,
            [{
                "company": "Acme", "exact_role": "Engineer",
                "vacancy_url": "https://example.com/job/007", "source": "getonboard",
                "listing_kind": "job",
            }],
        )
        assert len(result["created"]) == 1
        row = await session.get(Vacancy, result["created"][0]["id"])
        assert row.process_stage == "not_applied"
        assert row.process_stage_updated_at is not None
