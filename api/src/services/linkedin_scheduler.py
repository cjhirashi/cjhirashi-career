"""
Background scheduler for LinkedIn posts. LinkedIn's API has no native
scheduling (see linkedin_service.py docstring) - it always publishes
immediately - so this polls our own `linkedin_posts` table for rows past
their `scheduled_at` and publishes them itself. This *is* the "programar"
feature; there is no LinkedIn-side equivalent it's deferring to.

Runs as a single asyncio task in api_rest's own event loop (the service
runs with a single uvicorn worker, so there's no risk of two loops racing
to publish the same row).
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from database import AsyncSessionLocal
from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from services import linkedin_service
from services.linkedin_service import LinkedInError

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


async def _publish_due_posts() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(LinkedInPost).where(
                LinkedInPost.status == LinkedInPostStatus.SCHEDULED,
                LinkedInPost.scheduled_at <= datetime.now(timezone.utc),
            )
        )
        due_posts = result.scalars().all()
        if not due_posts:
            return

        for post in due_posts:
            connection_result = await db.execute(
                select(LinkedInConnection).where(LinkedInConnection.user_id == post.user_id)
            )
            connection = connection_result.scalar_one_or_none()

            if connection is None or connection.expires_at <= datetime.now(timezone.utc):
                post.status = LinkedInPostStatus.FAILED
                post.error_message = (
                    "La conexión con LinkedIn expiró antes de la fecha programada - "
                    "reconecta y vuelve a intentar."
                )
                logger.warning(f"Scheduled LinkedIn post {post.id} skipped: no valid connection")
                continue

            try:
                image_urn = None
                if post.image_url:
                    async with httpx.AsyncClient() as client:
                        image_response = await client.get(post.image_url)
                        image_response.raise_for_status()
                    image_urn = await linkedin_service.upload_image(
                        connection.access_token, connection.member_sub, image_response.content
                    )

                post_urn = await linkedin_service.create_post(
                    connection.access_token, connection.member_sub, post.text, image_urn
                )
                post.status = LinkedInPostStatus.PUBLISHED
                post.linkedin_post_urn = post_urn
                post.published_at = datetime.now(timezone.utc)
                logger.info(f"Published scheduled LinkedIn post {post.id}")
            except (LinkedInError, httpx.HTTPError) as e:
                logger.error(f"Scheduled LinkedIn post {post.id} failed: {e}")
                post.status = LinkedInPostStatus.FAILED
                post.error_message = str(e)

        await db.commit()


async def scheduler_loop() -> None:
    """Runs forever - intended to be started as a background asyncio task
    from app.py's lifespan and cancelled on shutdown."""
    while True:
        try:
            await _publish_due_posts()
        except Exception:
            logger.exception("LinkedIn scheduler tick failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
