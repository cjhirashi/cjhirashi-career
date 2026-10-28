"""vacancies.cv_version_id FK to cv_versions.

`recommended_cv_version` stays free text (useful to jot down a recommendation
before the formal CVVersion exists); `cv_version_id` is the optional, reliable
link once a real CV version was sent for this vacancy. Checked at the
model/schema level (no DB needed) — the migration itself (fa5fb4f6d183) is
exercised by `alembic upgrade`/`downgrade`, not unit tests.
"""
from models.vacancy import Vacancy
from schemas.career_search import VacancyBase, VacancyResponse, VacancyUpdate


def test_model_has_nullable_fk_to_cv_versions():
    column = Vacancy.__table__.c.cv_version_id
    assert column.nullable is True
    fks = list(column.foreign_keys)
    assert len(fks) == 1
    assert fks[0].target_fullname == "cv_versions.id"


def test_schemas_expose_cv_version_id():
    assert "cv_version_id" in VacancyBase.model_fields
    assert "cv_version_id" in VacancyUpdate.model_fields
    assert "cv_version_id" in VacancyResponse.model_fields
    assert not VacancyBase.model_fields["cv_version_id"].is_required()
