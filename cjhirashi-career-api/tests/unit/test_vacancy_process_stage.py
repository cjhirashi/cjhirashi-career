"""Spec 007 — Vacantes: etapa del proceso y estado calculado.

Bloque A: catálogo y reglas puras de `services/vacancy_stage.py`.
Bloque B: modelo `Vacancy` y schemas (`career_search`).
El canon de los valores es `contracts/process-stage-catalog.json` de la spec.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.vacancy import Vacancy
from schemas.career_search import VacancyCreate, VacancyResponse, VacancyUpdate
from services import vacancy_stage
from services.vacancy_stage import (
    PROCESS_STAGES,
    STAGE_TO_STATUS,
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
