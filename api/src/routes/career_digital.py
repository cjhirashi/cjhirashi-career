"""
Career domain (v2), Dominio 3: Presencia Digital.

Aggregates CRUD routers for: digital_platforms, content_pieces, publications.
"""
from fastapi import APIRouter

from models.digital_platform import DigitalPlatform
from models.content_piece import ContentPiece
from models.publication import Publication

from schemas.career_digital import (
    DigitalPlatformCreate, DigitalPlatformUpdate, DigitalPlatformResponse,
    ContentPieceCreate, ContentPieceUpdate, ContentPieceResponse,
    PublicationCreate, PublicationUpdate, PublicationResponse,
)

from routes.career_common import build_crud_router

router = APIRouter(prefix="/career", tags=["Career - Digital Presence"])

router.include_router(build_crud_router(
    prefix="/digital-platforms", tags=["Career - Digital Presence"], model=DigitalPlatform,
    create_schema=DigitalPlatformCreate, update_schema=DigitalPlatformUpdate,
    response_schema=DigitalPlatformResponse, entity_name="digital platform",
))

router.include_router(build_crud_router(
    prefix="/content-pieces", tags=["Career - Digital Presence"], model=ContentPiece,
    create_schema=ContentPieceCreate, update_schema=ContentPieceUpdate,
    response_schema=ContentPieceResponse, entity_name="content piece",
))

router.include_router(build_crud_router(
    prefix="/publications", tags=["Career - Digital Presence"], model=Publication,
    create_schema=PublicationCreate, update_schema=PublicationUpdate,
    response_schema=PublicationResponse, entity_name="publication",
))
