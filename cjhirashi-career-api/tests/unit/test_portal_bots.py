"""
Tests for portal_bots service.
"""
import pytest

from services.portal_bots import score_bot, is_bot, BOT_THRESHOLD


@pytest.mark.requisito("RF-007")
def test_score_bot_chrome_normal():
    """Chrome with language => score 0, no reasons."""
    score, reasons = score_bot(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0",
        accept_language="en-US,en;q=0.9",
        has_client_visitor_id=True,
        finished=False,
        pageviews=5,
        active_ms=60000,
        max_scroll_pct=50,
    )
    assert score == 0
    assert reasons == []


@pytest.mark.requisito("RF-007")
def test_score_bot_curl():
    """curl user agent => is_bot."""
    score, reasons = score_bot(
        user_agent="curl/7.68.0",
        accept_language=None,
        has_client_visitor_id=False,
        finished=True,
        pageviews=1,
        active_ms=100,
        max_scroll_pct=0,
    )
    assert is_bot(score)
    assert "ua_bot" in reasons


@pytest.mark.requisito("RF-007")
def test_score_bot_ua_missing_no_language():
    """UA missing + no language => 80."""
    score, reasons = score_bot(
        user_agent=None,
        accept_language=None,
        has_client_visitor_id=True,
        finished=False,
        pageviews=1,
        active_ms=1000,
        max_scroll_pct=0,
    )
    assert score == 80
    assert "ua_missing" in reasons
    assert "no_language" in reasons


@pytest.mark.requisito("RF-007")
def test_score_bot_no_interaction_only_with_finished():
    """no_interaction penalty only applied when finished=True."""
    # Without finished=True
    score, _ = score_bot(
        user_agent="Chrome/1.0",
        accept_language="en-US",
        has_client_visitor_id=True,
        finished=False,
        pageviews=1,
        active_ms=500,
        max_scroll_pct=0,
    )
    assert "no_interaction" not in score_bot(
        user_agent="Chrome/1.0",
        accept_language="en-US",
        has_client_visitor_id=True,
        finished=False,
        pageviews=1,
        active_ms=500,
        max_scroll_pct=0,
    )[1]

    # With finished=True
    score, reasons = score_bot(
        user_agent="Chrome/1.0",
        accept_language="en-US",
        has_client_visitor_id=True,
        finished=True,
        pageviews=1,
        active_ms=500,
        max_scroll_pct=0,
    )
    assert "no_interaction" in reasons


@pytest.mark.requisito("RF-007")
def test_score_bot_capped_at_100():
    """Bot score is capped at 100."""
    score, _ = score_bot(
        user_agent=None,
        accept_language=None,
        has_client_visitor_id=False,
        finished=True,
        pageviews=1,
        active_ms=500,
        max_scroll_pct=0,
    )
    assert score <= 100
    # ua_missing (60) + no_language (20) + no_visitor_id (10) + no_interaction (15) = 105 -> 100
    assert score == 100


@pytest.mark.requisito("RF-007")
def test_score_bot_order_of_reasons():
    """Reasons are listed in the order they were applied."""
    score, reasons = score_bot(
        user_agent=None,
        accept_language=None,
        has_client_visitor_id=False,
        finished=True,
        pageviews=1,
        active_ms=500,
        max_scroll_pct=0,
    )
    # Order should be: ua_missing, no_language, no_visitor_id, no_interaction
    expected_order = ["ua_missing", "no_language", "no_visitor_id", "no_interaction"]
    assert reasons == expected_order


@pytest.mark.requisito("RF-007")
def test_is_bot_threshold():
    """is_bot returns True for score >= BOT_THRESHOLD."""
    assert is_bot(70) is True
    assert is_bot(69) is False
    assert is_bot(100) is True
