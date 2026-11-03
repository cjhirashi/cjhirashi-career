"""
Posts de LinkedIn bajo `/career/linkedin-posts`.

Los tokens de agente solo alcanzan `/career/*` (middleware/auth.py), así que `/linkedin/*`
(OAuth y publicación del panel) les devolvía 403 y la tabla `linkedin_posts` no estaba en
el CRUD de carrera. Esta ruta da a los agentes la misma lista/publicación/programación,
con JSON en lugar de multipart, sobre la conexión de LinkedIn del dueño del portafolio.
Conectar o desconectar la cuenta (OAuth) sigue siendo solo del panel: requiere el navegador de Carlos.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from models.user import User
from schemas.linkedin import LinkedInPostResponse, LinkedInStatusResponse
from services import linkedin_service
from services.linkedin_service import LinkedInError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/career/linkedin-posts", tags=["Career - Digital Presence"])


class LinkedInPostCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    image_url: Optional[str] = Field(default=None, max_length=1024)
    scheduled_at: Optional[datetime] = Field(
        default=None, description="ISO 8601; sin zona se toma como UTC. Omitir publica ahora."
    )
    notes: Optional[str] = None


async def _connection(db: AsyncSession, user_id: str) -> LinkedInConnection | None:
    result = await db.execute(select(LinkedInConnection).where(LinkedInConnection.user_id == user_id))
    return result.scalar_one_or_none()


@router.get("/connection", response_model=LinkedInStatusResponse, summary="LinkedIn connection status")
async def connection_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conn = await _connection(db, current_user.id)
    if conn is None or conn.expires_at <= datetime.now(timezone.utc):
        return LinkedInStatusResponse(
            connected=False,
            member_name=conn.member_name if conn else None,
            expires_at=conn.expires_at if conn else None,
            notes="Sin conexión vigente: Carlos debe reconectar LinkedIn desde el panel (OAuth).",
        )
    return LinkedInStatusResponse(
        connected=True, member_name=conn.member_name, member_email=conn.member_email, expires_at=conn.expires_at
    )


@router.get("", response_model=list[LinkedInPostResponse], summary="List LinkedIn posts")
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(scheduled|published|failed)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LinkedInPost).where(LinkedInPost.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(LinkedInPost.status == status_filter)
    result = await db.execute(stmt.order_by(desc(LinkedInPost.created_at)).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{post_id}", response_model=LinkedInPostResponse, summary="Get a LinkedIn post")
async def get_post(post_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id, LinkedInPost.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("", response_model=LinkedInPostResponse, status_code=status.HTTP_201_CREATED, summary="Publish or schedule a LinkedIn post")
async def create_post(
    body: LinkedInPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await _connection(db, current_user.id)
    if conn is None or conn.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="LinkedIn is not connected or the connection has expired - Carlos must reconnect it from the panel",
        )

    scheduled_dt = body.scheduled_at
    if scheduled_dt is not None and scheduled_dt.tzinfo is None:
        scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)

    if scheduled_dt and scheduled_dt > datetime.now(timezone.utc):
        post = LinkedInPost(
            user_id=current_user.id, text=body.text, image_url=body.image_url,
            status=LinkedInPostStatus.SCHEDULED, scheduled_at=scheduled_dt, notes=body.notes,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    try:
        image_urn = None
        if body.image_url:
            async with httpx.AsyncClient(timeout=30) as client:
                image = await client.get(body.image_url)
                image.raise_for_status()
            image_urn = await linkedin_service.upload_image(conn.access_token, conn.member_sub, image.content)
        post_urn = await linkedin_service.create_post(conn.access_token, conn.member_sub, body.text, image_urn)
    except (LinkedInError, httpx.HTTPError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    post = LinkedInPost(
        user_id=current_user.id, text=body.text, image_url=body.image_url, status=LinkedInPostStatus.PUBLISHED,
        linkedin_post_urn=post_urn, published_at=datetime.now(timezone.utc), notes=body.notes,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel a scheduled LinkedIn post")
async def cancel_scheduled_post(post_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id, LinkedInPost.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.status != LinkedInPostStatus.SCHEDULED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a still-scheduled post can be canceled")
    await db.delete(post)
    await db.commit()
