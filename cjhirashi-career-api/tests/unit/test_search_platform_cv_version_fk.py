"""search_platforms.cv_version_id FK to cv_versions - the CV uploaded when
registering a profile on that platform. Checked at the model/schema level
(no DB needed) — the migration itself (fa5fb4f6d183) is exercised by
`alembic upgrade`/`downgrade`, not unit tests.
"""
from models.search_platform import SearchPlatform
from schemas.career_search import SearchPlatformBase, SearchPlatformResponse, SearchPlatformUpdate


def test_model_has_nullable_fk_to_cv_versions():
    column = SearchPlatform.__table__.c.cv_version_id
    assert column.nullable is True
    fks = list(column.foreign_keys)
    assert len(fks) == 1
    assert fks[0].target_fullname == "cv_versions.id"


def test_schemas_expose_cv_version_id():
    assert "cv_version_id" in SearchPlatformBase.model_fields
    assert "cv_version_id" in SearchPlatformUpdate.model_fields
    assert "cv_version_id" in SearchPlatformResponse.model_fields
    assert not SearchPlatformBase.model_fields["cv_version_id"].is_required()
