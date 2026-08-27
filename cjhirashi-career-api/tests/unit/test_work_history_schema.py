"""WorkHistory response must serialize JSONB scalars, not only objects."""
from datetime import datetime, timezone

from schemas.career_identity import WorkHistoryResponse


def _payload(**overrides):
    base = dict(
        id="wkh-1",
        user_id="usr-2",
        company="CYVSA",
        role_title="Gerente de Automatización",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return base


def test_response_accepts_string_key_metrics():
    row = WorkHistoryResponse.model_validate(
        _payload(key_metrics="- Equipo gestionado: 13 técnicos")
    )
    assert row.key_metrics == "- Equipo gestionado: 13 técnicos"


def test_response_accepts_object_key_metrics():
    row = WorkHistoryResponse.model_validate(_payload(key_metrics={"headcount": 13}))
    assert row.key_metrics == {"headcount": 13}


def test_response_accepts_null_key_metrics():
    row = WorkHistoryResponse.model_validate(_payload(key_metrics=None))
    assert row.key_metrics is None
