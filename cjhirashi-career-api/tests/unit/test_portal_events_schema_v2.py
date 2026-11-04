"""
Tests for portal events schema v2: backward compatibility with v1 + new fields.

Tests C1 requirements: schema accepts v1 payload, new v2 fields with validation,
UTM truncation/filtering, click IDs filtering, vitals filtering.
"""
import pytest
from pydantic import ValidationError

from schemas.events import TrackEventIn


@pytest.mark.requisito("RF-001")
class TestSchemaV1Compatibility:
    """Schema v2 must accept all v1 payloads without breaking."""

    def test_minimal_pageview_v1(self):
        """v1 minimal pageview (only type and page)."""
        event = TrackEventIn(type="pageview", page="/projects/test")
        assert event.type == "pageview"
        assert event.page == "/projects/test"
        assert event.target is None
        assert event.siteKey is None
        assert event.visitorId is None

    def test_full_v1_payload(self):
        """v1 payload with all optional fields."""
        event = TrackEventIn(
            type="click",
            page="/",
            target="button-submit",
            metadata={"foo": "bar"},
            sessionId="sess-abc123",
            durationMs=5000,
            timestamp="2026-11-04T10:00:00Z",
            userAgent="Mozilla/5.0",
            ip="8.8.8.8",
        )
        assert event.type == "click"
        assert event.page == "/"
        assert event.target == "button-submit"
        assert event.metadata == {"foo": "bar"}
        assert event.sessionId == "sess-abc123"
        assert event.durationMs == 5000
        assert event.timestamp == "2026-11-04T10:00:00Z"
        assert event.userAgent == "Mozilla/5.0"
        assert event.ip == "8.8.8.8"


@pytest.mark.requisito("RF-001")
class TestSchemaV2Fields:
    """Schema v2 new optional fields."""

    def test_site_key_and_visitor_id(self):
        """siteKey and visitorId are accepted."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            siteKey="abc123xyz456",
            visitorId="user-abc-123",
        )
        assert event.siteKey == "abc123xyz456"
        assert event.visitorId == "user-abc-123"

    def test_title_and_target_url(self):
        """title and targetUrl are accepted."""
        event = TrackEventIn(
            type="outbound",
            page="/",
            title="My Project",
            targetUrl="https://github.com/user/repo",
        )
        assert event.title == "My Project"
        assert event.targetUrl == "https://github.com/user/repo"

    def test_referrer_and_utm(self):
        """referrer and utm parameters are accepted."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            referrer="https://google.com",
            utm={
                "utm_source": "google",
                "utm_medium": "search",
                "utm_campaign": "campaign-1",
                "utm_content": "content-1",
                "utm_term": "keyword",
            },
        )
        assert event.referrer == "https://google.com"
        assert event.utm["utm_source"] == "google"
        assert event.utm["utm_medium"] == "search"

    def test_click_ids(self):
        """clickIds are accepted."""
        event = TrackEventIn(
            type="click",
            page="/",
            clickIds={
                "gclid": "abc123",
                "fbclid": "xyz789",
            },
        )
        assert event.clickIds["gclid"] == "abc123"
        assert event.clickIds["fbclid"] == "xyz789"

    def test_scroll_pct_and_active_ms(self):
        """scrollPct and activeMs are accepted."""
        event = TrackEventIn(
            type="scroll",
            page="/",
            scrollPct=75,
            activeMs=30000,
        )
        assert event.scrollPct == 75
        assert event.activeMs == 30000

    def test_screen_resolution(self):
        """screen is accepted."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            screen="1920x1080",
        )
        assert event.screen == "1920x1080"

    def test_owner_token(self):
        """ownerToken is accepted."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            ownerToken="secret-token-12345",
        )
        assert event.ownerToken == "secret-token-12345"

    def test_props_and_vitals(self):
        """props and vitals are accepted."""
        event = TrackEventIn(
            type="web_vitals",
            page="/",
            props={"custom": "value"},
            vitals={"lcp": 2500.0, "cls": 0.1, "inp": 100.0},
        )
        assert event.props["custom"] == "value"
        assert event.vitals["lcp"] == 2500.0
        assert event.vitals["cls"] == 0.1


@pytest.mark.requisito("RF-001")
class TestVisitorIdValidation:
    """visitorId must match [A-Za-z0-9_-] pattern."""

    def test_valid_visitor_id(self):
        """Valid visitorId patterns."""
        for vid in ["abc123", "user_123", "user-456", "ABC_DEF-789"]:
            event = TrackEventIn(type="pageview", page="/", visitorId=vid)
            assert event.visitorId == vid

    def test_invalid_visitor_id_with_spaces(self):
        """visitorId with spaces is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackEventIn(type="pageview", page="/", visitorId="user 123")
        assert "alphanumeric" in str(exc_info.value).lower()

    def test_invalid_visitor_id_with_special_chars(self):
        """visitorId with @, #, etc. is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", visitorId="user@123")

    def test_invalid_visitor_id_with_slash(self):
        """visitorId with / is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", visitorId="user/123")


@pytest.mark.requisito("RF-001")
class TestUTMFiltering:
    """UTM parameters are filtered to allowed keys and truncated to 255."""

    def test_utm_allowed_keys_only(self):
        """Only allowed UTM keys are kept."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            utm={
                "utm_source": "google",
                "utm_medium": "search",
                "utm_campaign": "campaign-1",
                "utm_content": "content",
                "utm_term": "keyword",
                "utm_random": "should-be-removed",
                "other_param": "ignored",
            },
        )
        allowed = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}
        assert set(event.utm.keys()) == allowed
        assert "utm_random" not in event.utm
        assert "other_param" not in event.utm

    def test_utm_truncated_to_255(self):
        """UTM values longer than 255 chars are truncated."""
        long_value = "x" * 500
        event = TrackEventIn(
            type="pageview",
            page="/",
            utm={
                "utm_source": long_value,
            },
        )
        assert len(event.utm["utm_source"]) == 255
        assert event.utm["utm_source"] == "x" * 255

    def test_empty_utm_returns_none(self):
        """If all UTM keys are filtered out, utm becomes None."""
        event = TrackEventIn(
            type="pageview",
            page="/",
            utm={
                "utm_random": "ignored",
                "other_param": "also-ignored",
            },
        )
        assert event.utm is None or event.utm == {}


@pytest.mark.requisito("RF-001")
class TestClickIDsFiltering:
    """Click IDs are filtered to allowed keys only."""

    def test_click_ids_allowed_keys_only(self):
        """Only allowed click ID keys are kept."""
        event = TrackEventIn(
            type="click",
            page="/",
            clickIds={
                "gclid": "gclid-abc",
                "fbclid": "fbclid-xyz",
                "msclkid": "msclkid-123",
                "ttclid": "ttclid-456",
                "twclid": "twclid-789",
                "li_fat_id": "li_fat_id-000",
                "random_id": "should-be-removed",
            },
        )
        allowed = {"gclid", "fbclid", "msclkid", "ttclid", "twclid", "li_fat_id"}
        assert set(event.clickIds.keys()) == allowed
        assert "random_id" not in event.clickIds

    def test_empty_click_ids_returns_none(self):
        """If all click IDs are filtered out, clickIds becomes None."""
        event = TrackEventIn(
            type="click",
            page="/",
            clickIds={
                "random_id": "ignored",
                "another_id": "also-ignored",
            },
        )
        assert event.clickIds is None or event.clickIds == {}


@pytest.mark.requisito("RF-001")
class TestVitalsFiltering:
    """Web Vitals are filtered to allowed keys and coerced to floats."""

    def test_vitals_allowed_keys_only(self):
        """Only allowed vitals keys are kept."""
        event = TrackEventIn(
            type="web_vitals",
            page="/",
            vitals={
                "lcp": 2500.0,
                "inp": 100.5,
                "cls": 0.1,
                "fcp": 1800.0,
                "ttfb": 500.0,
                "random_vital": 999.0,
            },
        )
        allowed = {"lcp", "inp", "cls", "fcp", "ttfb"}
        assert set(event.vitals.keys()) == allowed
        assert "random_vital" not in event.vitals

    def test_vitals_coerced_to_float(self):
        """Vitals are coerced to float."""
        event = TrackEventIn(
            type="web_vitals",
            page="/",
            vitals={
                "lcp": "2500",  # String
                "inp": 100,  # Int
                "cls": 0.1,  # Float
            },
        )
        assert isinstance(event.vitals["lcp"], float)
        assert isinstance(event.vitals["inp"], float)
        assert isinstance(event.vitals["cls"], float)

    def test_invalid_vitals_skipped(self):
        """Invalid vitals values are skipped."""
        event = TrackEventIn(
            type="web_vitals",
            page="/",
            vitals={
                "lcp": 2500.0,
                "inp": "not-a-number",
                "cls": 0.1,
            },
        )
        assert "lcp" in event.vitals
        assert "cls" in event.vitals
        assert "inp" not in event.vitals

    def test_empty_vitals_returns_none(self):
        """If all vitals are filtered out, vitals becomes None."""
        event = TrackEventIn(
            type="web_vitals",
            page="/",
            vitals={
                "random_vital": 999.0,
                "another_vital": "invalid",
            },
        )
        assert event.vitals is None or event.vitals == {}


@pytest.mark.requisito("RF-001")
class TestEventTypes:
    """All event types (v1 + v2) are accepted."""

    def test_v1_event_types(self):
        """v1 event types are still valid."""
        v1_types = ["pageview", "click", "download", "form_submit", "scroll", "page_duration"]
        for etype in v1_types:
            event = TrackEventIn(type=etype, page="/")
            assert event.type == etype

    def test_v2_event_types(self):
        """v2 event types are accepted."""
        v2_types = ["outbound", "project_open", "web_vitals", "page_leave"]
        for etype in v2_types:
            event = TrackEventIn(type=etype, page="/")
            assert event.type == etype

    def test_invalid_event_type(self):
        """Invalid event type is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="invalid-type", page="/")


@pytest.mark.requisito("RF-001")
class TestFieldConstraints:
    """Field size and range constraints."""

    def test_page_max_length(self):
        """page exceeding 500 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="x" * 501)

    def test_site_key_max_length(self):
        """siteKey exceeding 32 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", siteKey="x" * 33)

    def test_visitor_id_max_length(self):
        """visitorId exceeding 64 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", visitorId="x" * 65)

    def test_title_max_length(self):
        """title exceeding 500 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", title="x" * 501)

    def test_target_url_max_length(self):
        """targetUrl exceeding 1024 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", targetUrl="x" * 1025)

    def test_referrer_max_length(self):
        """referrer exceeding 1024 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", referrer="x" * 1025)

    def test_owner_token_max_length(self):
        """ownerToken exceeding 128 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", ownerToken="x" * 129)

    def test_screen_max_length(self):
        """screen exceeding 20 chars is rejected."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", screen="x" * 21)

    def test_scroll_pct_range(self):
        """scrollPct must be 0-100."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", scrollPct=101)
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", scrollPct=-1)
        event = TrackEventIn(type="pageview", page="/", scrollPct=0)
        assert event.scrollPct == 0
        event = TrackEventIn(type="pageview", page="/", scrollPct=100)
        assert event.scrollPct == 100

    def test_active_ms_range(self):
        """activeMs must be 0 to 86400000 (24h)."""
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", activeMs=-1)
        with pytest.raises(ValidationError):
            TrackEventIn(type="pageview", page="/", activeMs=86_400_001)
        event = TrackEventIn(type="pageview", page="/", activeMs=0)
        assert event.activeMs == 0
        event = TrackEventIn(type="pageview", page="/", activeMs=86_400_000)
        assert event.activeMs == 86_400_000
