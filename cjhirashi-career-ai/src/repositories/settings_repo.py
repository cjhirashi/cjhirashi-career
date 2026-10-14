"""
Repositorio de `bedrock_settings` (fila única de operador: prompt, reglas, modelo, límites).

Traslado de `settings_loader.py` y de `get/set_system_prompt`, `get/set_global_rules` de
`bedrock_service.py` (API). Solo persistencia: el valor por defecto de prompt/reglas y los
defaults de configuración se resuelven en los servicios.
"""
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_settings import BedrockSettings

_UPDATABLE_FIELDS = frozenset(
    {
        "system_prompt",
        "global_rules",
        "active_model_id",
        "orchestrator_model_id",
        "max_round_trips",
        "history_window",
        "daily_budget_usd",
    }
)


async def get_settings(db: AsyncSession) -> Optional[BedrockSettings]:
    result = await db.execute(select(BedrockSettings).limit(1))
    return result.scalar_one_or_none()


async def update_settings(db: AsyncSession, **fields: Any) -> BedrockSettings:
    """Actualiza (creando la fila en el primer uso) solo los campos indicados."""
    unknown = set(fields) - _UPDATABLE_FIELDS
    if unknown:
        raise ValueError(f"Campos no actualizables en bedrock_settings: {sorted(unknown)}")
    row = await get_settings(db)
    if row is None:
        row = BedrockSettings(**fields)
        db.add(row)
    else:
        for name, value in fields.items():
            setattr(row, name, value)
    await db.commit()
    await db.refresh(row)
    return row


async def get_system_prompt_override(db: AsyncSession) -> Optional[str]:
    row = await get_settings(db)
    return row.system_prompt if row and row.system_prompt else None


async def set_system_prompt(db: AsyncSession, text: Optional[str]) -> Optional[str]:
    """Fija (o, con `None`, limpia) el override. Devuelve el override resultante."""
    row = await update_settings(db, system_prompt=text)
    return row.system_prompt or None


async def get_global_rules_override(db: AsyncSession) -> Optional[str]:
    row = await get_settings(db)
    return row.global_rules if row and row.global_rules else None


async def set_global_rules(db: AsyncSession, text: Optional[str]) -> Optional[str]:
    row = await update_settings(db, global_rules=text)
    return row.global_rules or None


async def set_active_model_id(db: AsyncSession, model_id: str) -> None:
    await update_settings(db, active_model_id=model_id)
