"""
Career domain (v2), Dominio 4: Soporte.

Aggregates CRUD router for: tags.
"""
from fastapi import APIRouter

from models.tag import Tag
from schemas.career_support import TagCreate, TagUpdate, TagResponse
from routes.career_common import build_crud_router

router = APIRouter(prefix="/career", tags=["Career - Support"])

router.include_router(build_crud_router(
    prefix="/tags", tags=["Career - Support"], model=Tag,
    create_schema=TagCreate, update_schema=TagUpdate,
    response_schema=TagResponse, entity_name="tag",
))
