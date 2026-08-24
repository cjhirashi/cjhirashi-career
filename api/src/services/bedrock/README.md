# Paquete `services/bedrock/`

Harness local Agent Bedrock. Ver [docs/BEDROCK-SYSTEM.md](../../../docs/BEDROCK-SYSTEM.md).

| Módulo | Responsabilidad |
|--------|-----------------|
| `agent_loop.py` | Loop Converse + SSE events |
| `converse_client.py` | Cliente ConverseStream |
| `tools.py` | Schemas y ejecución tools |
| `history_manager.py` | Conversaciones PG |
| `agent_profiles.py` | 9 perfiles especialista |
| `section_profiles.py` | Modelo recomendado por sección |
| `delegation.py` | Sub-turnos orquestador |
| `budget.py` | Presupuesto diario USD |
| `usage_logger.py` | Logs por turno y round |
| `prompt.py` | System prompt compuesto |
| `settings_loader.py` | bedrock_settings runtime |
| `image_client.py` | Titan Image Generator |
| `embeddings.py` | Titan Embeddings |
