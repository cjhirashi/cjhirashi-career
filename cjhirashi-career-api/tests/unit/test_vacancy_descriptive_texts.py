"""Spec 008 — Vacantes: cuatro textos descriptivos (empresa, perfil, oferta, cultura).

Bloque A: schemas (trim, vacío -> None, tope de 10 000 tras el trim).
Bloque B: modelo. Bloque C: repositorio y KB. Bloque D: ruta HTTP.
Sin Postgres, Bedrock ni Qdrant reales (SQLite en memoria, indexación neutralizada).
"""
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from models.vacancy import Vacancy
from repositories.career_repository import CareerRepository
from schemas.career_search import VacancyCreate, VacancyResponse, VacancyUpdate

FIELDS = ("company_overview", "candidate_profile", "offer_summary", "work_culture")
BASE = {"company": "ACME", "exact_role": "Dev"}
LIMIT = 10_000
USER = "usr-1"


# ---------------------------------------------------------------------------
# Bloque A — schemas
# ---------------------------------------------------------------------------

@pytest.mark.requisito("RF-002")
@pytest.mark.requisito("RF-003")
def test_create_and_update_accept_the_four_fields():
    values = {f: f"texto {f}" for f in FIELDS}
    assert VacancyCreate(**BASE, **values).model_dump()["work_culture"] == "texto work_culture"
    upd = VacancyUpdate(**values)
    assert all(getattr(upd, f) == values[f] for f in FIELDS)


@pytest.mark.requisito("RF-004")
@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("raw", ["", "   ", "\n\t", " \r\n "])
def test_blank_values_become_none_in_create_and_update(field, raw):
    assert getattr(VacancyCreate(**BASE, **{field: raw}), field) is None
    upd = VacancyUpdate(**{field: raw})
    assert getattr(upd, field) is None
    assert field in upd.model_fields_set  # vacío explícito = borrar


@pytest.mark.requisito("RF-004")
@pytest.mark.parametrize("field", FIELDS)
def test_trim_only_at_the_edges_keeps_inner_content(field):
    assert getattr(VacancyCreate(**BASE, **{field: "  hola  "}), field) == "hola"
    rich = "Línea 1\n\n- viñeta 🚀\n- otra"
    assert getattr(VacancyCreate(**BASE, **{field: f"\n {rich} \n"}), field) == rich
    assert getattr(VacancyUpdate(**{field: f"  {rich}  "}), field) == rich


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("field", FIELDS)
def test_length_limit_is_measured_after_trim(field):
    ok = "a" * LIMIT
    assert getattr(VacancyCreate(**BASE, **{field: ok}), field) == ok
    assert getattr(VacancyUpdate(**{field: f"   {ok}   "}), field) == ok
    for schema, extra in ((VacancyCreate, BASE), (VacancyUpdate, {})):
        with pytest.raises(ValidationError):
            schema(**extra, **{field: "a" * (LIMIT + 1)})


@pytest.mark.requisito("RF-002")
def test_response_exposes_the_four_keys_with_none():
    resp = VacancyResponse(
        id="vac-1", user_id=USER, process_stage_updated_at="2026-10-13T00:00:00Z",
        created_at="2026-10-13T00:00:00Z", updated_at="2026-10-13T00:00:00Z", **BASE,
    )
    dumped = resp.model_dump()
    assert all(f in dumped and dumped[f] is None for f in FIELDS)


@pytest.mark.requisito("RF-003")
def test_update_omitted_field_is_not_set_but_explicit_null_is():
    assert VacancyUpdate(company="X").model_dump(exclude_unset=True) == {"company": "X"}
    assert VacancyUpdate(work_culture=None).model_dump(exclude_unset=True) == {"work_culture": None}


# ---------------------------------------------------------------------------
# Bloque B — modelo
# ---------------------------------------------------------------------------

@pytest.fixture
def vacancy_session():
    engine = create_engine("sqlite:///:memory:")
    Vacancy.__table__.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-002")
def test_model_persists_and_rereads_long_multiline_text(vacancy_session):
    long_text = "\n".join(f"línea {i} " + "x" * 60 for i in range(100))
    assert len(long_text) >= 5_000
    vacancy_session.add(
        Vacancy(id="vac-1", user_id=USER, company="A", exact_role="B",
                **{f: long_text for f in FIELDS})
    )
    vacancy_session.add(Vacancy(id="vac-2", user_id=USER, company="A", exact_role="B"))
    vacancy_session.commit()
    vacancy_session.expire_all()
    full = vacancy_session.get(Vacancy, "vac-1")
    assert all(getattr(full, f) == long_text for f in FIELDS)
    empty = vacancy_session.get(Vacancy, "vac-2")
    assert all(getattr(empty, f) is None for f in FIELDS)


# ---------------------------------------------------------------------------
# Bloque C — repositorio y KB
# ---------------------------------------------------------------------------

@pytest.fixture
async def repo_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Vacancy.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    repo = CareerRepository(Vacancy, resource_key="vacancies")

    async def _no_index(obj, user_id):  # sin Qdrant ni Bedrock (RNF-002)
        return None

    repo._index_for_search = _no_index
    async with factory() as session:
        yield repo, session
    await engine.dispose()


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-003")
async def test_repo_create_update_persist_fields_and_leave_others_untouched(repo_env):
    repo, session = repo_env
    values = {f: f"valor {f}" for f in FIELDS}
    vac = await repo.create_for_user(session, USER, {"id": "vac-1", **BASE, **values})
    assert all(getattr(vac, f) == values[f] for f in FIELDS)
    upd = await repo.update_for_user(session, USER, "vac-1", {"company": "Otra"})
    assert upd.company == "Otra"
    assert all(getattr(upd, f) == values[f] for f in FIELDS)
    upd = await repo.update_for_user(session, USER, "vac-1", {"work_culture": "nueva"})
    assert upd.work_culture == "nueva"
    assert upd.offer_summary == values["offer_summary"]


@pytest.mark.requisito("RF-004")
@pytest.mark.requisito("RF-005")
async def test_repo_via_tools_applies_no_trim_nor_limit_d07(repo_env):
    """D-07 (caracterización, no contrato): la vía de las tools Bedrock no pasa por
    Pydantic, así que no hay trim ni tope; la spec 009 mueve esa escritura a REST."""
    repo, session = repo_env
    huge = "  " + "a" * (LIMIT + 1) + "  "
    vac = await repo.create_for_user(session, USER, {"id": "vac-1", **BASE, "company_overview": huge})
    assert vac.company_overview == huge


@pytest.mark.requisito("RF-006")
def test_kb_text_excludes_the_four_fields_but_keeps_stage_and_notes():
    repo = CareerRepository(Vacancy, resource_key="vacancies")
    vac = Vacancy(
        id="vac-kb", user_id=USER, company="ACME", exact_role="Dev",
        process_stage="hr_interview", analysis_notes="notas visibles",
        company_overview="SECRETO-EMPRESA", candidate_profile="SECRETO-PERFIL",
        offer_summary="SECRETO-OFERTA", work_culture="SECRETO-CULTURA",
    )
    text_ = repo._record_to_text(vac)
    for f in FIELDS:
        assert f not in text_
    for secret in ("SECRETO-EMPRESA", "SECRETO-PERFIL", "SECRETO-OFERTA", "SECRETO-CULTURA"):
        assert secret not in text_
    assert "process_stage: hr_interview" in text_
    assert "analysis_notes: notas visibles" in text_
    assert "process_stage_updated_at" not in text_  # no regresión 007 D-13


# ---------------------------------------------------------------------------
# Bloque D — ruta HTTP `/career/vacancies` (SQLite en memoria, JWT real)
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
            username="u008", email="u008@example.com", password_hash="x",
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
        yield client
    app_module.app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


async def _post(client, **extra):
    resp = await client.post("/career/vacancies", json={**BASE, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _get(client, vid):
    resp = await client.get(f"/career/vacancies/{vid}")
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-002")
@pytest.mark.parametrize("field", FIELDS)
async def test_http_each_field_alone_and_all_four(http_env, field):
    client = http_env
    body = await _post(client, **{field: "valor"})
    assert body[field] == "valor"
    assert all(body[f] is None for f in FIELDS if f != field)
    assert (await _get(client, body["id"]))[field] == "valor"
    put = await client.put(f"/career/vacancies/{body['id']}", json={field: "otro"})
    assert put.status_code == 200 and put.json()[field] == "otro"
    assert (await _get(client, body["id"]))[field] == "otro"


@pytest.mark.requisito("RF-001")
async def test_http_four_fields_at_once_and_without_target_company(http_env):
    client = http_env
    values = {f: f"texto\n\n- {f}" for f in FIELDS}
    body = await _post(client, **values)
    assert body["target_company_id"] is None
    assert {f: body[f] for f in FIELDS} == values
    assert {f: (await _get(client, body["id"]))[f] for f in FIELDS} == values


@pytest.mark.requisito("RF-002")
async def test_http_response_without_values_has_null_keys(http_env):
    client = http_env
    body = await _post(client)
    assert all(f in body and body[f] is None for f in FIELDS)
    listing = (await client.get("/career/vacancies")).json()
    items = listing["items"] if isinstance(listing, dict) and "items" in listing else listing
    assert all(f in items[0] and items[0][f] is None for f in FIELDS)


@pytest.mark.requisito("RF-003")
async def test_http_put_other_field_does_not_touch_the_texts(http_env):
    client = http_env
    values = {f: f"valor {f}" for f in FIELDS}
    body = await _post(client, **values)
    put = await client.put(f"/career/vacancies/{body['id']}", json={"company": "Nueva"})
    assert put.status_code == 200 and put.json()["company"] == "Nueva"
    assert {f: put.json()[f] for f in FIELDS} == values
    put = await client.put(f"/career/vacancies/{body['id']}", json={"offer_summary": "x"})
    assert {f: put.json()[f] for f in FIELDS if f != "offer_summary"} == {
        f: values[f] for f in FIELDS if f != "offer_summary"
    }


@pytest.mark.requisito("RF-003")
@pytest.mark.requisito("RF-004")
@pytest.mark.parametrize("cleared", [None, "", "   ", "\n\t"])
async def test_http_null_empty_or_blank_clears_the_field(http_env, cleared):
    client = http_env
    body = await _post(client, work_culture="algo", offer_summary="queda")
    put = await client.put(f"/career/vacancies/{body['id']}", json={"work_culture": cleared})
    assert put.status_code == 200 and put.json()["work_culture"] is None
    got = await _get(client, body["id"])
    assert got["work_culture"] is None and got["offer_summary"] == "queda"


@pytest.mark.requisito("RF-004")
async def test_http_blank_on_create_is_null_and_text_is_trimmed(http_env):
    client = http_env
    body = await _post(client, company_overview="   ", candidate_profile="  hola \n")
    assert body["company_overview"] is None
    assert body["candidate_profile"] == "hola"


@pytest.mark.requisito("RF-005")
async def test_http_limit_10000_ok_10001_is_422_and_row_unchanged(http_env):
    client = http_env
    body = await _post(client, work_culture="a" * LIMIT)
    assert len(body["work_culture"]) == LIMIT
    ok = await _post(client, company_overview=" " + "b" * LIMIT + " ")
    assert len(ok["company_overview"]) == LIMIT

    bad = await client.put(f"/career/vacancies/{body['id']}", json={"work_culture": "c" * (LIMIT + 1)})
    assert bad.status_code == 422
    payload = bad.json()
    assert "detail" in payload and "errors" in payload
    assert (await _get(client, body["id"]))["work_culture"] == "a" * LIMIT

    bad_post = await client.post("/career/vacancies", json={**BASE, "offer_summary": "d" * (LIMIT + 1)})
    assert bad_post.status_code == 422
