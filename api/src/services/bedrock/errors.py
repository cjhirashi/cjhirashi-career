"""
Errores del Harness local Bedrock.

Centraliza excepciones que las rutas FastAPI convierten en HTTP 502/503.
Ver docs/BEDROCK-SYSTEM.md y ADR-008.
"""


class BedrockError(Exception):
    """Fallo recuperable o de configuración en inferencia, tools o presupuesto."""

    pass


class BedrockBudgetExceeded(BedrockError):
    """Presupuesto diario de inferencia agotado — ver bedrock/budget.py."""

    pass
