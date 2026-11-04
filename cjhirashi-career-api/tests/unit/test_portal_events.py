"""portal_events ingestion: schema validation and model columns (no network, no DB)."""
from models.portal_event import PortalEvent
from schemas.events import TrackEventIn


def test_track_event_in_accepts_minimal_pageview():
    event = TrackEventIn(type="pageview", page="/projects/some-slug")
    assert event.type == "pageview"
    assert event.target is None


def test_track_event_in_rejects_unknown_type():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TrackEventIn(type="not-a-real-type", page="/")


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
