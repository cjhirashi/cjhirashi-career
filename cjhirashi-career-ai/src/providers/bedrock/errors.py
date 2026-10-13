"""Errores del proveedor Bedrock y formateo de errores de botocore (traslado de api/services/bedrock/errors.py)."""
from botocore.exceptions import ClientError

from providers.base import ProviderError


class BedrockError(ProviderError):
    """Fallo recuperable o de configuración en inferencia o generación de imágenes."""


def format_bedrock_client_error(exc: Exception, *, model_id: str) -> str:
    """Mensaje legible para errores boto3 Bedrock (IAM, modelo, cuota, throttling)."""
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
                "Revisa el catálogo de modelos del proveedor y permisos IAM. "
                f"Detalle: {message}"
            )
        return f"Error Bedrock ({code}): {message}"
    return f"Converse request failed: {exc}"
