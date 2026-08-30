"""Fotos de agentes del catálogo (URL pública del bucket)."""
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_system_profile_photos import AgentSystemProfilePhoto
from services.bedrock.agent_profiles import get_profile


async def photos_map(db: AsyncSession) -> Dict[str, str]:
    result = await db.execute(select(AgentSystemProfilePhoto))
    return {row.profile_id: row.photo_url for row in result.scalars().all() if row.photo_url}


async def set_photo(db: AsyncSession, profile_id: str, photo_url: Optional[str]) -> dict:
    profile = get_profile(profile_id)
    url = (photo_url or "").strip() or None
    result = await db.execute(
        select(AgentSystemProfilePhoto).where(AgentSystemProfilePhoto.profile_id == profile.id)
    )
    row = result.scalar_one_or_none()
    if not url:
        if row:
            await db.delete(row)
            await db.commit()
        return {"profile_id": profile.id, "photo_url": None}
    if row:
        row.photo_url = url
    else:
        db.add(AgentSystemProfilePhoto(profile_id=profile.id, photo_url=url))
    await db.commit()
    return {"profile_id": profile.id, "photo_url": url}
