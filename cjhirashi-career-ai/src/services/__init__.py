"""
Paquete Harness Bedrock — motor del agente IA del Admin Panel.

Componentes principales:
- agent_loop.chat_stream — loop Converse + tools + SSE
- converse_client — streaming Bedrock
- tools — CRUD career, LinkedIn, job discovery, imágenes
- history_manager / local_memory — historial PG + Qdrant
"""

from services.agent_loop import chat_stream
from services.errors import BedrockBudgetExceeded, BedrockError

__all__ = ["chat_stream", "BedrockError", "BedrockBudgetExceeded"]
