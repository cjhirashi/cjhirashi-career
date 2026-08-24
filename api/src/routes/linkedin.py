"""
LinkedIn integration routes - connect/disconnect the account (OAuth) and
publish posts through the self-serve "Share on LinkedIn" product.

`/callback` is deliberately the only route here with no `get_current_user`
dependency: it's reached via a plain browser redirect from LinkedIn with no
Authorization header, so the user is identified from the signed `state`
token instead (see services/linkedin_service.py).
"""
import io
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from models.user import User
from schemas.linkedin import (
    LinkedInConnectResponse,
    LinkedInPostResponse,
    LinkedInStatusResponse,
)
from services import linkedin_service, storage_service
from services.linkedin_service import LinkedInError
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


async def _get_connection(db: AsyncSession, user_id: str) -> LinkedInConnection | None:
    result = await db.execute(select(LinkedInConnection).where(LinkedInConnection.user_id == user_id))
    return result.scalar_one_or_none()


@router.get("/status", response_model=LinkedInStatusResponse)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_connection(db, current_user.id)
    if connection is None or connection.expires_at <= datetime.now(timezone.utc):
        return LinkedInStatusResponse(connected=False)

    return LinkedInStatusResponse(
        connected=True,
        member_name=connection.member_name,
        member_email=connection.member_email,
        profile_picture_url=connection.profile_picture_url,
        expires_at=connection.expires_at,
    )


@router.get("/connect", response_model=LinkedInConnectResponse)
async def connect(current_user: User = Depends(get_current_user)):
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn integration is not configured (missing LINKEDIN_CLIENT_ID/LINKEDIN_REDIRECT_URI)",
        )
    return LinkedInConnectResponse(authorize_url=linkedin_service.build_authorize_url(current_user.id))


@router.get("/callback")
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    frontend_url = settings.LINKEDIN_FRONTEND_URL or "/"

    if error or not code or not state:
        return RedirectResponse(f"{frontend_url}?linkedin_error={error or 'missing_code'}")

    try:
        user_id = linkedin_service.decode_state_token(state)
        token_data = await linkedin_service.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 60 * 24 * 3600)
        userinfo = await linkedin_service.fetch_userinfo(access_token)
    except LinkedInError as e:
        logger.error(f"LinkedIn callback failed: {e}")
        return RedirectResponse(f"{frontend_url}?linkedin_error=1")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    connection = await _get_connection(db, user_id)
    if connection is None:
        connection = LinkedInConnection(user_id=user_id)
        db.add(connection)

    connection.access_token = access_token
    connection.member_sub = userinfo["sub"]
    connection.member_name = userinfo.get("name")
    connection.member_email = userinfo.get("email")
    connection.profile_picture_url = userinfo.get("picture")
    connection.expires_at = expires_at

    await db.commit()

    return RedirectResponse(f"{frontend_url}?linkedin_connected=1")


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_connection(db, current_user.id)
    if connection is not None:
        await db.delete(connection)
        await db.commit()


@router.get("/posts", response_model=list[LinkedInPostResponse])
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LinkedInPost)
        .where(LinkedInPost.user_id == current_user.id)
        .order_by(desc(LinkedInPost.created_at))
        .limit(20)
    )
    return result.scalars().all()


@router.post("/posts", response_model=LinkedInPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    text: str = Form(..., min_length=1, max_length=3000),
    scheduled_at: str | None = Form(default=None, description="ISO datetime - omit to publish immediately"),
    image: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connection = await _get_connection(db, current_user.id)
    if connection is None or connection.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="LinkedIn is not connected or the connection has expired - reconnect first",
        )

    image_bytes: bytes | None = None
    image_url: str | None = None
    if image is not None:
        image_bytes = await image.read()
        # Keep our own public copy too - LinkedIn's own upload isn't a
        # stable URL we can redisplay in the history list below, and a
        # scheduled post needs these bytes again later when it's actually
        # published (see linkedin_scheduler.py).
        stored_filename = storage_service.upload_file(
            data=io.BytesIO(image_bytes),
            original_filename=image.filename or "image",
            size=len(image_bytes),
            content_type=image.content_type or "image/jpeg",
            category="linkedin-posts",
            is_public=True,
        )
        image_url = storage_service.get_public_url(stored_filename)

    scheduled_dt: datetime | None = None
    if scheduled_at:
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid scheduled_at")
        if scheduled_dt.tzinfo is None:
            scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)

    if scheduled_dt and scheduled_dt > datetime.now(timezone.utc):
        post = LinkedInPost(
            user_id=current_user.id,
            text=text,
            image_url=image_url,
            status=LinkedInPostStatus.SCHEDULED,
            scheduled_at=scheduled_dt,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    try:
        image_urn = None
        if image_bytes:
            image_urn = await linkedin_service.upload_image(
                connection.access_token, connection.member_sub, image_bytes
            )
        post_urn = await linkedin_service.create_post(
            connection.access_token, connection.member_sub, text, image_urn
        )
    except LinkedInError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    post = LinkedInPost(
        user_id=current_user.id,
        text=text,
        image_url=image_url,
        status=LinkedInPostStatus.PUBLISHED,
        linkedin_post_urn=post_urn,
        published_at=datetime.now(timezone.utc),
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id, LinkedInPost.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.status != LinkedInPostStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a still-scheduled (not yet published) post can be canceled",
        )
    await db.delete(post)
    await db.commit()
