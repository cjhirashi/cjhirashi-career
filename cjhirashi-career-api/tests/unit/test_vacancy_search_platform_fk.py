"""vacancies.search_platform_id FK to search_platforms.

`source` stays free text; `search_platform_id` is the optional, reliable
link to a platform with a tracked profile. Checked at the model/schema level
(no DB needed) — the migration itself (8d756b313e88) is exercised by
`alembic upgrade`/`downgrade`, not unit tests.
"""
from models.vacancy import Vacancy
from schemas.career_search import VacancyBase, VacancyResponse, VacancyUpdate


def test_model_has_nullable_fk_to_search_platforms():
    column = Vacancy.__table__.c.search_platform_id
    assert column.nullable is True
    fks = list(column.foreign_keys)
    assert len(fks) == 1
    assert fks[0].target_fullname == "search_platforms.id"


def test_schemas_expose_search_platform_id():
    assert "search_platform_id" in VacancyBase.model_fields
    assert "search_platform_id" in VacancyUpdate.model_fields
    assert "search_platform_id" in VacancyResponse.model_fields
    # source sigue siendo texto libre y opcional; search_platform_id también opcional.
    assert not VacancyBase.model_fields["search_platform_id"].is_required()
