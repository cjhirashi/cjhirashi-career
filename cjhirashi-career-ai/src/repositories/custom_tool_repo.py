"""Repositorio de `bedrock_custom_tools` (servidores MCP remotos). Traslado de `bedrock_service.py` (API)."""
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_custom_tool import BedrockCustomTool


async def list_custom_tools(db: AsyncSession) -> List[BedrockCustomTool]:
    result = await db.execute(select(BedrockCustomTool).order_by(BedrockCustomTool.created_at.desc()))
    return list(result.scalars().all())


async def get_custom_tool(db: AsyncSession, tool_id: str) -> Optional[BedrockCustomTool]:
    result = await db.execute(select(BedrockCustomTool).where(BedrockCustomTool.id == tool_id))
    return result.scalar_one_or_none()


async def create_custom_tool(
    db: AsyncSession, name: str, url: str, headers: Optional[Dict[str, str]] = None
) -> BedrockCustomTool:
    tool = BedrockCustomTool(name=name, url=url, headers=headers or None, is_enabled=True)
    db.add(tool)
    await db.flush()
    await db.refresh(tool)
    await db.commit()
    return tool


async def set_custom_tool_enabled(db: AsyncSession, tool_id: str, is_enabled: bool) -> Optional[BedrockCustomTool]:
    tool = await get_custom_tool(db, tool_id)
    if tool is None:
        return None
    tool.is_enabled = is_enabled
    await db.commit()
    await db.refresh(tool)
    return tool


async def delete_custom_tool(db: AsyncSession, tool_id: str) -> bool:
    tool = await get_custom_tool(db, tool_id)
    if tool is None:
        return False
    await db.delete(tool)
    await db.commit()
    return True
