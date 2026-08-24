"""
BedrockCustomTool — servidores MCP remotos registrados por el operador.

Solo `remote_mcp` está soportado. Las tools builtin (CRUD, LinkedIn, PDF, etc.)
viven en services/bedrock/tools.py. Ver routes/bedrock.py /tools.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class BedrockCustomTool(Base):
    __tablename__ = "bedrock_custom_tools"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True)
    # --- Campos de negocio ---
    name = Column(String(100), nullable=False, unique=True)
    url = Column(Text, nullable=False)
    headers = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<BedrockCustomTool(id={self.id}, name='{self.name}')>"

register_id_listener(BedrockCustomTool, "bct")
