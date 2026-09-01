"""Tests for Bedrock error message formatting."""

from botocore.exceptions import ClientError

from services.errors import format_bedrock_client_error


def _client_error(code: str, message: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "Converse")


def test_validation_conversation_must_start_with_user():
    exc = _client_error(
        "ValidationException",
        "A conversation must start with a user message. Try again with a conversation that starts with a user message.",
    )
    msg = format_bedrock_client_error(exc, model_id="amazon.nova-lite-v1:0")
    assert "historial enviado a Bedrock es inválido" in msg
    assert "no disponible" not in msg.lower() or "Model access" not in msg


def test_validation_other_shows_validation_label():
    exc = _client_error("ValidationException", "Invalid tool schema")
    msg = format_bedrock_client_error(exc, model_id="amazon.nova-lite-v1:0")
    assert "Error de validación Bedrock" in msg


def test_resource_not_found_shows_model_unavailable():
    exc = _client_error("ResourceNotFoundException", "Model not found")
    msg = format_bedrock_client_error(exc, model_id="amazon.nova-lite-v1:0")
    assert "no disponible o no habilitado" in msg


def test_access_denied_mentions_iam():
    exc = _client_error(
        "AccessDeniedException",
        "not authorized to perform: bedrock:InvokeModel on resource: arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    msg = format_bedrock_client_error(exc, model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    assert "Permisos IAM insuficientes" in msg
    assert "us-east-2" in msg
