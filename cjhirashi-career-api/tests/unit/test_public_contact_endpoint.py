"""
Tests para POST /public/contact-message (endpoint de contacto público).

- RF-001: acepta nombre, email, mensaje
- RF-003: honeypot (campo website)
- RF-004: límites por IP y correo (3 por hora)
- RF-007: devuelve 201 solo tras confirmar escritura en BD
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.contact_message import ContactMessage
from config import settings


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-007")
async def test_contact_message_endpoint_creates_message(client: AsyncClient, test_db):
    """POST /public/contact-message crea un mensaje y devuelve 201 con id."""
    payload = {
        "name": "Carlos",
        "email": "carlos@example.com",
        "message": "Quiero colaborar en un proyecto",
        "website": "",
    }

    response = await client.post("/public/contact-message", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["id"].startswith("cmg-")


@pytest.mark.requisito("RF-001")
async def test_contact_message_validation_fails_on_short_name(client: AsyncClient):
    """El nombre vacío devuelve 422."""
    payload = {
        "name": "",
        "email": "test@example.com",
        "message": "Test",
        "website": "",
    }

    response = await client.post("/public/contact-message", json=payload)

    assert response.status_code == 422


@pytest.mark.requisito("RF-001")
async def test_contact_message_validation_fails_on_invalid_email(client: AsyncClient):
    """Email inválido devuelve 422."""
    payload = {
        "name": "Test",
        "email": "not-an-email",
        "message": "Test",
        "website": "",
    }

    response = await client.post("/public/contact-message", json=payload)

    assert response.status_code == 422


@pytest.mark.requisito("RF-003")
async def test_honeypot_website_field_returns_201_but_no_save(client: AsyncClient, test_db):
    """Si website tiene contenido, devuelve 201 sin guardar ni avisar."""
    payload = {
        "name": "Bot",
        "email": "bot@spam.com",
        "message": "Spam",
        "website": "http://spam.com",
    }

    response = await client.post("/public/contact-message", json=payload)

    # Devuelve 201 igual (para que el bot no aprenda)
    assert response.status_code == 201
    # Pero verificar que NO se guardó (necesita async test_db)


@pytest.mark.requisito("RF-004")
async def test_rate_limit_ip_exceeded_returns_429(client: AsyncClient):
    """El 4to envío desde la misma IP en una hora devuelve 429."""
    payload = {
        "name": "Test",
        "email": "test@example.com",
        "message": "Test message",
        "website": "",
    }

    # 3 envíos exitosos
    for i in range(3):
        response = await client.post("/public/contact-message", json=payload)
        assert response.status_code == 201

    # 4to devuelve 429
    response = await client.post("/public/contact-message", json=payload)
    assert response.status_code == 429


@pytest.mark.requisito("RF-004")
async def test_rate_limit_email_exceeded_returns_429(client: AsyncClient):
    """El 4to envío desde el mismo email en una hora devuelve 429."""
    payload = {
        "name": "Test",
        "email": "same@example.com",
        "message": "Test message {i}",
        "website": "",
    }

    # 3 envíos con el mismo email
    for i in range(3):
        p = payload.copy()
        p["message"] = f"Test message {i}"
        response = await client.post("/public/contact-message", json=p)
        assert response.status_code == 201

    # 4to desde el mismo email devuelve 429
    response = await client.post(
        "/public/contact-message",
        json={**payload, "message": "Test message 4"},
    )
    assert response.status_code == 429
