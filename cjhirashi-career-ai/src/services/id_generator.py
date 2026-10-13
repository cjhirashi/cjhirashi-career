"""
Generación de IDs prefijados para las tablas del harness.

Formato: {PREFIX}-{n} con n tomado de la secuencia `{prefix}_id_seq` de Postgres.
Copia mínima de la API (solo los 5 prefijos del harness). Las secuencias las crea la
migración 0001; el script de copia las ajusta con `setval` (hazard de secuencias).
"""
from sqlalchemy import event, text

TABLE_PREFIXES: dict[str, str] = {
    "bedrock_conversations": "bco",
    "bedrock_conversation_messages": "bcm",
    "bedrock_custom_tools": "bct",
    "bedrock_tasks": "btk",
    "bedrock_agent_memory": "bam",
}


def _seq_name(table_name: str) -> str:
    return f"{TABLE_PREFIXES[table_name]}_id_seq"


def register_id_listener(model_class, prefix: str) -> None:
    """Registra `before_insert`: asigna `prefix-nextval` si el modelo no trae id."""
    table_name = model_class.__tablename__

    @event.listens_for(model_class, "before_insert")
    def _assign_id(mapper, connection, target):
        if not target.id:
            n = connection.execute(text(f"SELECT nextval('{_seq_name(table_name)}')")).scalar()
            target.id = f"{prefix}-{n}"
