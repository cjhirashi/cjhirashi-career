"""SPEC-0011: formulario de contacto del portafolio (POST público + recurso Admin)."""
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app import app
from config import settings
from database import get_db
from middleware.auth import get_current_user
from models import ContactMessage, User, UserNotification
from routes import public

OWNER = settings.PUBLIC_PORTAL_USER_ID
VALID = {"name": "Ana", "email": "ana@example.com", "message": "Hola, quiero hablar de un proyecto"}


def _user(user_id: str, username: str) -> User:
    return User(id=user_id, username=username, email=f"{username}@example.com", password_hash="x", is_active=True)


@pytest.fixture
async def client(test_db):
    async with test_db() as setup:
        setup.add(_user(OWNER, "owner"))
        setup.add(_user("usr-other-0011", "other"))
        await setup.commit()

    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    public._ip_limiter._hits.clear()
    public._email_limiter._hits.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        c.test_db = test_db
        yield c
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def as_owner(client):
    async with client.test_db() as s:
        owner = (await s.execute(select(User).where(User.id == OWNER))).scalar_one()
    app.dependency_overrides[get_current_user] = lambda: owner
    return client


async def _rows(client, model):
    async with client.test_db() as s:
        return (await s.execute(select(model))).scalars().all()


async def _post(client, payload=None, ip="198.51.100.1"):
    return await client.post("/public/contact-message", json=payload or VALID, headers={"cf-connecting-ip": ip})


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-002")
@pytest.mark.requisito("RF-005")
async def test_message_is_stored_and_owner_notified(client):
    r = await _post(client, {**VALID, "name": "  Ana  ", "message": "  Hola  "})
    assert r.status_code == 201
    msg_id = r.json()["id"]
    assert msg_id.startswith("cmg-")

    (row,) = await _rows(client, ContactMessage)
    assert (row.id, row.user_id, row.name, row.message, row.status) == (msg_id, OWNER, "Ana", "Hola", "new")
    assert row.read_at is None

    (note,) = await _rows(client, UserNotification)
    assert (note.user_id, note.kind, note.resource_key, note.resource_id) == (OWNER, "contact_message", "contact-messages", msg_id)
    assert "Ana" in note.title


@pytest.mark.requisito("RF-002")
def test_no_ip_or_header_column_is_persisted():
    cols = {c.name for c in ContactMessage.__table__.columns}
    assert cols == {"id", "user_id", "name", "email", "message", "status", "read_at", "created_at"}


@pytest.mark.requisito("RF-001")
@pytest.mark.parametrize("patch_", [
    {"name": ""},
    {"email": "no-es-correo"},
    {"message": ""},
    {"message": "x" * 5001},
    {"name": "x" * 121},
])
async def test_invalid_payload_is_rejected(client, patch_):
    r = await _post(client, {**VALID, **patch_})
    assert r.status_code == 422
    assert await _rows(client, ContactMessage) == []


@pytest.mark.requisito("RF-003")
async def test_honeypot_returns_201_without_storing_or_notifying(client):
    r = await _post(client, {**VALID, "website": "http://spam.example"})
    assert r.status_code == 201
    assert await _rows(client, ContactMessage) == []
    assert await _rows(client, UserNotification) == []


@pytest.mark.requisito("RF-004")
async def test_fourth_message_from_same_ip_gets_429(client):
    for i in range(3):
        assert (await _post(client, {**VALID, "email": f"u{i}@example.com"})).status_code == 201
    r = await _post(client, {**VALID, "email": "u9@example.com"})
    assert r.status_code == 429
    assert len(await _rows(client, ContactMessage)) == 3


@pytest.mark.requisito("RF-004")
async def test_fourth_message_with_same_email_gets_429(client):
    for i in range(3):
        assert (await _post(client, ip=f"198.51.100.{i + 10}")).status_code == 201
    assert (await _post(client, ip="198.51.100.99")).status_code == 429


@pytest.mark.requisito("RF-005")
async def test_notification_failure_does_not_lose_the_message(client):
    with patch("routes.public.ContactMessageService._create_notification", side_effect=RuntimeError("boom")):
        r = await _post(client)
    assert r.status_code == 201
    assert len(await _rows(client, ContactMessage)) == 1


@pytest.mark.requisito("RF-001")
async def test_storage_failure_returns_5xx_not_success(client):
    with patch("routes.public.ContactMessageService.save_contact_message", side_effect=RuntimeError("db down")):
        r = await _post(client)
    assert r.status_code == 500


# ----------------------------------------------------------------------------
# Admin
# ----------------------------------------------------------------------------
@pytest.mark.requisito("RF-006")
async def test_admin_requires_auth(client):
    assert (await client.get("/career/contact-messages")).status_code in (401, 403)


@pytest.mark.requisito("RF-006")
async def test_admin_lists_only_own_messages_newest_first_and_filters_status(as_owner):
    c = as_owner
    ids = [(await _post(c, {**VALID, "email": f"u{i}@example.com"}, ip=f"198.51.100.{i}")).json()["id"] for i in range(2)]
    async with c.test_db() as s:
        s.add(ContactMessage(user_id="usr-other-0011", name="Otro", email="o@example.com", message="privado"))
        await s.commit()

    r = await c.get("/career/contact-messages", params={"sort_by": "created_at", "sort_dir": "desc"})
    assert r.status_code == 200
    assert [m["id"] for m in r.json()] == ids[::-1]

    await c.put(f"/career/contact-messages/{ids[0]}", json={"status": "archived"})
    r = await c.get("/career/contact-messages", params={"filters": '{"status": "new"}'})
    assert [m["id"] for m in r.json()] == [ids[1]]


@pytest.mark.requisito("RF-006")
async def test_admin_marking_read_stamps_read_at_and_rejects_other_fields(as_owner):
    c = as_owner
    msg_id = (await _post(c)).json()["id"]

    r = await c.put(f"/career/contact-messages/{msg_id}", json={"status": "read"})
    assert r.status_code == 200
    assert r.json()["status"] == "read"
    assert r.json()["read_at"] is not None

    r = await c.put(f"/career/contact-messages/{msg_id}", json={"status": "read", "name": "Hacker"})
    assert r.status_code == 422
    r = await c.put(f"/career/contact-messages/{msg_id}", json={"status": "inexistente"})
    assert r.status_code == 422
    (row,) = await _rows(c, ContactMessage)
    assert row.name == "Ana"


@pytest.mark.requisito("RF-006")
async def test_admin_cannot_create_and_can_delete(as_owner):
    c = as_owner
    assert (await c.post("/career/contact-messages", json=VALID)).status_code == 405
    msg_id = (await _post(c)).json()["id"]
    assert (await c.delete(f"/career/contact-messages/{msg_id}")).status_code == 204
    assert (await c.get(f"/career/contact-messages/{msg_id}")).status_code == 404
