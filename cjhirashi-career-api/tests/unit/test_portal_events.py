"""portal_events ingestion: schema validation and the public/private IP guard
in geo_ip_service (no network, no DB - the ipapi.co call itself is exercised
manually, not in CI).
"""
from models.portal_event import PortalEvent
from schemas.events import TrackEventIn
from services.geo_ip_service import _is_public_ip


def test_track_event_in_accepts_minimal_pageview():
    event = TrackEventIn(type="pageview", page="/projects/some-slug")
    assert event.type == "pageview"
    assert event.target is None


def test_track_event_in_rejects_unknown_type():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TrackEventIn(type="not-a-real-type", page="/")


def test_is_public_ip_rejects_private_and_loopback():
    assert _is_public_ip("127.0.0.1") is False
    assert _is_public_ip("10.0.0.5") is False
    assert _is_public_ip("172.18.0.3") is False
    assert _is_public_ip("not-an-ip") is False


def test_is_public_ip_accepts_public_address():
    assert _is_public_ip("8.8.8.8") is True


def test_portal_event_model_columns():
    columns = PortalEvent.__table__.c
    assert columns.event_type.nullable is False
    assert columns.page.nullable is False
    assert columns.country.nullable is True
    # "metadata" would collide with SQLAlchemy's declarative Base attribute -
    # the column is named event_metadata specifically to avoid that.
    assert "event_metadata" in columns
    assert "metadata" not in columns
    assert columns.latitude.nullable is True
    assert columns.longitude.nullable is True
