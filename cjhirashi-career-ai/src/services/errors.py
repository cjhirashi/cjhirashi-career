"""
Errores del Harness local Bedrock.

Centraliza excepciones que las rutas FastAPI convierten en HTTP 502/503.
Ver docs/BEDROCK-SYSTEM.md y ADR-008.
"""

from botocore.exceptions import ClientError


# ============================================================================
# Excepciones del harness
# ============================================================================

class BedrockError(Exception):
    """Fallo recuperable o de configuración en inferencia, tools o presupuesto."""

    pass


class BedrockBudgetExceeded(BedrockError):
    """Presupuesto diario de inferencia agotado — ver bedrock/budget.py."""

    pass


# ============================================================================
# Formateo de errores boto3
# ============================================================================

def format_bedrock_client_error(exc: Exception, *, model_id: str) -> str:
    """Mensaje legible para errores boto3 Bedrock (IAM, modelo, cuota)."""
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        message = exc.response.get("Error", {}).get("Message", str(exc))
        if code == "AccessDeniedException":
            if "InvokeModelWithResponseStream" in message:
                action = "bedrock:InvokeModelWithResponseStream"
            else:
                action = "bedrock:InvokeModel"
            return (
                f"Permisos IAM insuficientes en AWS Bedrock ({action}) para el modelo "
                f"'{model_id}'. El usuario IAM (p. ej. portafolio-bedrock-agent) necesita "
                "política con inference profiles y foundation models en us-east-1, "
                "us-east-2 y us-west-2 (ver api/docs/BEDROCK-HARNESS.md#iam). "
                f"Detalle AWS: {message}"
            )
        if code == "ValidationException":
            if "conversation must start with a user message" in message.lower():
                return (
                    "El historial enviado a Bedrock es inválido (debe empezar con un mensaje "
                    f"de usuario). Modelo: '{model_id}'. Detalle AWS: {message}"
                )
            return f"Error de validación Bedrock ({model_id}): {message}"
        if code == "ResourceNotFoundException":
            return (
                f"Modelo Bedrock no disponible o no habilitado: '{model_id}'. "
                "Revisa el catálogo en api/src/config.py y permisos IAM. "
                f"Detalle: {message}"
            )
        return f"Error Bedrock ({code}): {message}"
    return f"Converse request failed: {exc}"

