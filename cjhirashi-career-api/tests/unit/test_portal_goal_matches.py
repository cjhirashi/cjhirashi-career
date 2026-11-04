"""Quick test to verify portal_ingest imports and basic structure."""
import pytest
from services.portal_ingest import ingest_event, UnknownSite, goal_matches


def test_ingest_module_imports():
    """Verify the portal_ingest module can be imported."""
    assert ingest_event is not None
    assert UnknownSite is not None
    assert goal_matches is not None


def test_goal_matches_event_type():
    """Test goal_matches function for event type goals."""
    result = goal_matches(
        "event",
        {"event_type": "download"},
        event_type="download",
        page="/",
        target_url=None,
    )
    assert result is True

    result = goal_matches(
        "event",
        {"event_type": "download"},
        event_type="pageview",
        page="/",
        target_url=None,
    )
    assert result is False


def test_goal_matches_outbound():
    """Test goal_matches function for outbound goals."""
    result = goal_matches(
        "outbound",
        {"url_contains": "github"},
        event_type="outbound",
        page="/",
        target_url="https://github.com/user/repo",
    )
    assert result is True

    result = goal_matches(
        "outbound",
        {"url_contains": "github"},
        event_type="click",
        page="/",
        target_url="https://github.com/user/repo",
    )
    assert result is False


def test_goal_matches_page():
    """Test goal_matches function for page goals."""
    result = goal_matches(
        "page",
        {"path_prefix": "/projects/"},
        event_type="pageview",
        page="/projects/my-project",
        target_url=None,
    )
    assert result is True

    result = goal_matches(
        "page",
        {"path_prefix": "/projects/"},
        event_type="pageview",
        page="/about",
        target_url=None,
    )
    assert result is False
