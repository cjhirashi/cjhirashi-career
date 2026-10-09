"""vacancies.target_company_id FK to target_companies (checklist Paulina #6).

`company` stays free text; `target_company_id` is the optional, reliable
link to an already-researched target company. Checked at the model/schema
level (no DB needed) — the migration itself (a2b3c4d5e6f7) is exercised by
`alembic upgrade`/`downgrade`, not unit tests.
"""
from models.vacancy import Vacancy
from schemas.career_search import VacancyBase, VacancyResponse, VacancyUpdate


def test_model_has_nullable_fk_to_target_companies():
    column = Vacancy.__table__.c.target_company_id
    assert column.nullable is True
    fks = list(column.foreign_keys)
    assert len(fks) == 1
    assert fks[0].target_fullname == "target_companies.id"


def test_schemas_expose_target_company_id():
    assert "target_company_id" in VacancyBase.model_fields
    assert "target_company_id" in VacancyUpdate.model_fields
    assert "target_company_id" in VacancyResponse.model_fields
    # company sigue siendo obligatorio (texto libre); target_company_id es opcional.
    assert VacancyBase.model_fields["company"].is_required()
    assert not VacancyBase.model_fields["target_company_id"].is_required()
