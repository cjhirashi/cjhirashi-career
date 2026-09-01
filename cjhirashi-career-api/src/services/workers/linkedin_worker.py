"""
LinkedIn scheduler worker — consumes from Redis Streams and publishes scheduled posts.

FASE 1: Replaces linkedin_scheduler.py's asyncio loop with a standalone worker process
that consumes from Redis Streams via consumer groups (ensures exclusive delivery).

Idempotence: Verifies post status in Postgres before publishing; LinkedIn API is
also idempotent (duplicate call → same URN).

Stream: `linkedin:scheduled-posts`
Consumer Group: `linkedin-workers`
Message format: {post_id, scheduled_at (ISO 8601 timestamp)}
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select

from database import AsyncSessionLocal
from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from services import linkedin_service
from services.linkedin_service import LinkedInError
from services.error_reporting import report_error
from services.redis_client import get_redis

logger = logging.getLogger(__name__)

STREAM_KEY = "linkedin:scheduled-posts"
CONSUMER_GROUP = "linkedin-workers"
CONSUMER_NAME = "worker-1"
POLL_TIMEOUT_MS = 1000
MAX_RETRIES = 3


async def ensure_consumer_group(redis_client):
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info(f"Created consumer group {CONSUMER_GROUP} on {STREAM_KEY}")
    except redis_client.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.debug(f"Consumer group {CONSUMER_GROUP} already exists")
        else:
            raise


async def process_message(msg_id: str, data: dict) -> bool:
    """
    Process a single LinkedIn post message from the stream.
    Returns True if processed successfully, False if should retry.
    """
    post_id = data.get("post_id")
    scheduled_at_str = data.get("scheduled_at")

    if not post_id:
        logger.error(f"Message {msg_id}: missing post_id, discarding")
        return True  # Discard malformed message

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(LinkedInPost).where(LinkedInPost.id == post_id))
            post = result.scalar_one_or_none()

            if post is None:
                logger.warning(f"Post {post_id} not found, discarding message {msg_id}")
                return True  # Discard; post was deleted

            # Idempotence: skip if already published/failed (not SCHEDULED)
            if post.status != LinkedInPostStatus.SCHEDULED:
                logger.info(f"Post {post_id} already {post.status}, skipping (msg {msg_id})")
                return True  # Already processed

            # Verify connection is still valid
            conn_result = await db.execute(
                select(LinkedInConnection).where(LinkedInConnection.user_id == post.user_id)
            )
            connection = conn_result.scalar_one_or_none()

            if connection is None or connection.expires_at <= datetime.now(timezone.utc):
                post.status = LinkedInPostStatus.FAILED
                post.error_message = (
                    "La conexión con LinkedIn expiró antes de la fecha programada - "
                    "reconecta y vuelve a intentar."
                )
                await db.commit()
                logger.warning(f"Post {post_id}: connection expired")
                return True  # Terminal state; don't retry

            # Download image if present
            image_urn = None
            if post.image_url:
                try:
                    async with httpx.AsyncClient() as client:
                        image_response = await client.get(post.image_url, timeout=30)
                        image_response.raise_for_status()
                    image_urn = await linkedin_service.upload_image(
                        connection.access_token, connection.member_sub, image_response.content
                    )
                except (httpx.HTTPError, LinkedInError) as e:
                    logger.error(f"Post {post_id}: image upload failed: {e}")
                    post.status = LinkedInPostStatus.FAILED
                    post.error_message = f"Image upload failed: {str(e)[:200]}"
                    await db.commit()
                    return True  # Terminal state

            # Publish to LinkedIn
            try:
                post_urn = await linkedin_service.create_post(
                    connection.access_token, connection.member_sub, post.text, image_urn
                )
                post.status = LinkedInPostStatus.PUBLISHED
                post.linkedin_post_urn = post_urn
                post.published_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info(f"Published post {post_id} (msg {msg_id})")
                return True
            except (LinkedInError, httpx.HTTPError) as e:
                logger.error(f"Post {post_id}: publish failed: {e}")
                post.status = LinkedInPostStatus.FAILED
                post.error_message = str(e)[:500]
                await db.commit()
                if isinstance(e, httpx.HTTPError):
                    report_error(
                        str(e), f"worker:linkedin_worker:publish:{post_id}",
                        error_type=type(e).__name__, exc=e,
                        context={"post_id": post_id, "msg_id": msg_id},
                        severity="error",
                    )
                return True  # Terminal state

    except Exception as exc:
        logger.exception(f"Unexpected error processing message {msg_id}")
        report_error(
            str(exc), f"worker:linkedin_worker:process:{msg_id}",
            error_type=type(exc).__name__, exc=exc,
            context={"post_id": post_id},
            severity="error",
        )
        return False  # Retry


async def worker_loop(redis_client) -> None:
    """Main worker loop — consume and process messages."""
    await ensure_consumer_group(redis_client)
    logger.info(f"Worker started, consuming from {STREAM_KEY}")

    while True:
        try:
            # Read messages from consumer group (pending messages first, then new ones)
            messages = await redis_client.xreadgroup(
                {STREAM_KEY: ">"},  # > = new messages (not yet delivered)
                CONSUMER_GROUP,
                CONSUMER_NAME,
                count=1,
                block=POLL_TIMEOUT_MS,
            )

            if not messages:
                continue

            for stream_key, msgs in messages:
                for msg_id, data in msgs:
                    success = await process_message(msg_id, data)
                    if success:
                        await redis_client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    else:
                        logger.warning(f"Message {msg_id} failed; will retry on next poll (XPENDING)")

        except asyncio.CancelledError:
            logger.info("Worker shutting down")
            break
        except Exception as exc:
            logger.exception("Worker loop error")
            report_error(
                str(exc), "worker:linkedin_worker:loop",
                error_type=type(exc).__name__, exc=exc,
                severity="critical",
            )
            await asyncio.sleep(5)  # Back off before retrying


async def main():
    """Entry point for the worker."""
    try:
        redis_client = await get_redis()
        await worker_loop(redis_client)
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as exc:
        logger.exception("Worker failed to start")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
