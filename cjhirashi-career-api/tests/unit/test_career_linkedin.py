"""Posts de LinkedIn bajo /career/linkedin-posts: conexión vigente, programar, publicar y cancelar."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from routes import career_linkedin
from routes.career_linkedin import LinkedInPostCreate

NOW = datetime.now(timezone.utc)


def _user():
    user = MagicMock()
    user.id = "usr-2"
    return user


def _conn(expires_at):
    conn = MagicMock()
    conn.access_token = "tok"
    conn.member_sub = "sub"
    conn.member_name = "Carlos"
    conn.member_email = None
    conn.expires_at = expires_at
    return conn


def _db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create_without_valid_connection_is_409():
    for conn in (None, _conn(NOW - timedelta(days=1))):
        with patch.object(career_linkedin, "_connection", AsyncMock(return_value=conn)):
            with pytest.raises(HTTPException) as err:
                await career_linkedin.create_post(LinkedInPostCreate(text="hola"), _user(), _db())
        assert err.value.status_code == 409


@pytest.mark.asyncio
async def test_future_post_is_scheduled_without_calling_linkedin():
    db = _db()
    body = LinkedInPostCreate(text="mañana", scheduled_at=NOW + timedelta(days=1))
    with patch.object(career_linkedin, "_connection", AsyncMock(return_value=_conn(NOW + timedelta(days=30)))), \
         patch.object(career_linkedin.linkedin_service, "create_post", AsyncMock()) as create:
        await career_linkedin.create_post(body, _user(), db)
    create.assert_not_called()
    saved = db.add.call_args.args[0]
    assert saved.status == LinkedInPostStatus.SCHEDULED and saved.scheduled_at == body.scheduled_at


@pytest.mark.asyncio
async def test_naive_scheduled_at_is_taken_as_utc():
    db = _db()
    future = (NOW + timedelta(days=2)).replace(tzinfo=None)
    with patch.object(career_linkedin, "_connection", AsyncMock(return_value=_conn(NOW + timedelta(days=30)))):
        await career_linkedin.create_post(LinkedInPostCreate(text="x", scheduled_at=future), _user(), db)
    assert db.add.call_args.args[0].scheduled_at.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_publish_now_stores_urn():
    db = _db()
    with patch.object(career_linkedin, "_connection", AsyncMock(return_value=_conn(NOW + timedelta(days=30)))), \
         patch.object(career_linkedin.linkedin_service, "create_post", AsyncMock(return_value="urn:li:share:1")) as create:
        await career_linkedin.create_post(LinkedInPostCreate(text="ahora"), _user(), db)
    create.assert_awaited_once_with("tok", "sub", "ahora", None)
    saved = db.add.call_args.args[0]
    assert saved.status == LinkedInPostStatus.PUBLISHED and saved.linkedin_post_urn == "urn:li:share:1"


@pytest.mark.asyncio
async def test_linkedin_error_is_502_and_nothing_saved():
    db = _db()
    err = career_linkedin.LinkedInError("rechazado")
    with patch.object(career_linkedin, "_connection", AsyncMock(return_value=_conn(NOW + timedelta(days=30)))), \
         patch.object(career_linkedin.linkedin_service, "create_post", AsyncMock(side_effect=err)):
        with pytest.raises(HTTPException) as e:
            await career_linkedin.create_post(LinkedInPostCreate(text="x"), _user(), db)
    assert e.value.status_code == 502
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_only_scheduled_posts_can_be_canceled():
    db = _db()
    published = LinkedInPost(id="lnp-1", user_id="usr-2", text="x", status=LinkedInPostStatus.PUBLISHED)
    result = MagicMock()
    result.scalar_one_or_none.return_value = published
    db.execute = AsyncMock(return_value=result)
    with pytest.raises(HTTPException) as e:
        await career_linkedin.cancel_scheduled_post("lnp-1", _user(), db)
    assert e.value.status_code == 409
    db.delete.assert_not_called()


@pytest.mark.asyncio
async def test_connection_status_reports_expired():
    expired = _conn(NOW - timedelta(days=16))
    with patch.object(career_linkedin, "_connection", AsyncMock(return_value=expired)):
        out = await career_linkedin.connection_status(_user(), _db())
    assert out.connected is False and "reconectar" in out.notes
