"""
Storage Service - MinIO (S3-compatible) object storage for uploaded files.
Implements Single Responsibility Principle (bucket I/O only, no DB access).
"""
import json
import logging
import uuid
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from config import settings

logger = logging.getLogger(__name__)

_client: Optional[Minio] = None


def get_client() -> Minio:
    """Lazily create the MinIO client - internal Docker network traffic, no TLS needed
    (the public HTTPS endpoint is terminated by Caddy in cjhirashi-srv, not here)."""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
    return _client


def ensure_bucket() -> None:
    """Create the bucket if missing and make it publicly readable - called once at
    app startup. Public *read* only: uploads/deletes still always go through this
    service (and therefore through JWT auth), anonymous access can only GET objects
    it already knows the key for, e.g. an image linked from a Markdown field."""
    client = get_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
        logger.info("Created MinIO bucket '%s'", settings.MINIO_BUCKET)

    public_read_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"],
            }
        ],
    }
    client.set_bucket_policy(settings.MINIO_BUCKET, json.dumps(public_read_policy))


def upload_file(data: BinaryIO, original_filename: str, size: int, content_type: str) -> str:
    """Upload a file, returning the unique object key it was stored under
    (never the original filename, to avoid collisions/overwrites)."""
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    stored_filename = f"{uuid.uuid4().hex}.{extension}" if extension else uuid.uuid4().hex

    get_client().put_object(
        settings.MINIO_BUCKET,
        stored_filename,
        data,
        length=size,
        content_type=content_type or "application/octet-stream",
    )
    return stored_filename


def delete_file(stored_filename: str) -> bool:
    """Delete an object. Returns False (instead of raising) if it was already gone,
    since the caller's DB row is the source of truth for whether it 'exists'."""
    try:
        get_client().remove_object(settings.MINIO_BUCKET, stored_filename)
        return True
    except S3Error as e:
        if e.code == "NoSuchKey":
            return False
        raise


def get_public_url(stored_filename: str) -> str:
    return f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{stored_filename}"
