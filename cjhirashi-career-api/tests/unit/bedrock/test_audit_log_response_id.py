"""La bitácora del agente devuelve el id entero de `audit_logs` como texto.

Sin la conversión, `GET /bedrock/audit-log` respondía 500 en cuanto el agente
había escrito algo (ResponseValidationError: el id llegaba como entero).
"""
from datetime import datetime, timezone
from types import SimpleNamespace

from schemas.bedrock import BedrockAuditLogResponse


def test_audit_log_response_serializes_integer_id_as_text():
    row = SimpleNamespace(
        id=7,
        action="UPDATE",
        resource_type="vacancies",
        resource_id="vac-2",
        old_values={"process_stage": "screening"},
        new_values={"process_stage": "technical_interview"},
        created_at=datetime(2026, 11, 10, 18, 0, tzinfo=timezone.utc),
        notes=None,
    )
    out = BedrockAuditLogResponse.model_validate(row)
    assert out.id == "7"
