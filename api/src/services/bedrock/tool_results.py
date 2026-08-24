"""
Truncado de resultados de tools — control de tokens de entrada.

Ver docs/BEDROCK-SYSTEM.md § costos.
"""
import json
from typing import Any, Dict

from config import settings


def truncate_tool_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Serializa y trunca si supera BEDROCK_MAX_TOOL_RESULT_CHARS."""
    text = json.dumps(result, ensure_ascii=False, default=str)
    limit = settings.BEDROCK_MAX_TOOL_RESULT_CHARS
    if len(text) <= limit:
        return result
    return {
        "truncated": True,
        "preview": text[: limit - 80],
        "message": f"Resultado truncado a {limit} caracteres. Usa filtros más específicos.",
    }
