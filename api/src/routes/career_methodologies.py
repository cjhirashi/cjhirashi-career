"""
Career domain (v2), Dominio 5: Metodologías Operativas.

Aggregates CRUD router for: operational_methodologies.
"""
from fastapi import APIRouter

from models.operational_methodology import OperationalMethodology
from schemas.career_methodologies import (
    OperationalMethodologyCreate, OperationalMethodologyUpdate, OperationalMethodologyResponse,
)
from routes.career_common import build_crud_router

router = APIRouter(prefix="/career", tags=["Career - Methodologies"])

router.include_router(build_crud_router(
    prefix="/operational-methodologies", tags=["Career - Methodologies"], model=OperationalMethodology,
    create_schema=OperationalMethodologyCreate, update_schema=OperationalMethodologyUpdate,
    response_schema=OperationalMethodologyResponse, entity_name="operational methodology",
))
