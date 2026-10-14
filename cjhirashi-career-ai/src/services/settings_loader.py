"""Ajustes de runtime del agente: fila única de `bedrock_settings` con respaldo en la configuración.

Traslado de `cjhirashi-career-api/src/services/bedrock/settings_loader.py`; la lectura va por
`repositories.settings_repo` (el servicio solo decide los defaults).
"""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from repositories import settings_repo


@dataclass
class HarnessRuntimeSettings:
    active_model_id: str
    orchestrator_model_id: str
    max_round_trips: int
    history_window: int
    daily_budget_usd: float


async def get_runtime_settings(db: AsyncSession) -> HarnessRuntimeSettings:
    row = await settings_repo.get_settings(db)
    return HarnessRuntimeSettings(
        active_model_id=(row.active_model_id if row and row.active_model_id else settings.BEDROCK_DEFAULT_MODEL_ID),
        orchestrator_model_id=(
            row.orchestrator_model_id if row and row.orchestrator_model_id else settings.BEDROCK_ORCHESTRATOR_MODEL_ID
        ),
        max_round_trips=row.max_round_trips if row else settings.BEDROCK_MAX_ROUND_TRIPS,
        history_window=row.history_window if row else settings.BEDROCK_HISTORY_WINDOW,
        daily_budget_usd=float(row.daily_budget_usd if row else settings.BEDROCK_DAILY_BUDGET_USD),
    )


async def get_active_model_id(db: AsyncSession) -> str:
    return (await get_runtime_settings(db)).active_model_id
