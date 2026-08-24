"""
BedrockCustomTool Model - operator-registered MCP tool servers, merged into
the agent's tool list at invoke time alongside the built-in CRUD/knowledge-
base tools (see `services/bedrock_service.py::_active_tools`). This is how
Carlos adds new capabilities without a code deploy: point the agent at a
remote MCP server and its tools become available on the next chat turn.

Only `remote_mcp` today - the harness's other tool types (`agentcore_browser`,
`agentcore_code_interpreter`, `agentcore_gateway`) aren't wired up here since
nothing requested them; `inline_function` tools always need executor code we
write, so they aren't operator-addable the same way.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class BedrockCustomTool(Base):
    __tablename__ = "bedrock_custom_tools"

    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    url = Column(Text, nullable=False)
    headers = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<BedrockCustomTool(id={self.id}, name='{self.name}')>"

register_id_listener(BedrockCustomTool, "bct")
