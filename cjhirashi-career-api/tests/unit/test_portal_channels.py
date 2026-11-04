"""
Tests for portal_channels service.
"""
import pytest

from services.portal_channels import extract_domain, classify_channel


# ============================================================================
# B1.1: extract_domain tests
# ============================================================================


def test_extract_domain_full_url():
    """Extract domain from a full URL with scheme."""
    assert extract_domain("https://www.example.com/path?query=1") == "example.com"


def test_extract_domain_without_www():
    """Extract domain without www prefix."""
    assert extract_domain("https://example.com") == "example.com"


def test_extract_domain_with_port():
    """Extract domain, stripping port."""
    assert extract_domain("https://example.com:8080/path") == "example.com"


def test_extract_domain_lowercase():
    """Domain is normalized to lowercase."""
    assert extract_domain("https://EXAMPLE.COM") == "example.com"


def test_extract_domain_www_prefix_removed():
    """www. prefix is removed."""
    assert extract_domain("www.example.com") == "example.com"
    assert extract_domain("WWW.example.com") == "example.com"


def test_extract_domain_empty():
    """Empty or None input returns None."""
    assert extract_domain("") is None
    assert extract_domain(None) is None
    assert extract_domain("   ") is None


def test_extract_domain_invalid():
    """Invalid domain returns None."""
    assert extract_domain("://") is None


# ============================================================================
# B1.2: classify_channel tests
# ============================================================================


SEED_RULES = [
    {"priority": 0, "channel": "Application", "conditions": {"utm_medium_in": ["postulacion", "application"]}},
    {"priority": 1, "channel": "Email", "conditions": {"utm_medium_in": ["email", "e-mail", "e_mail"]}},
    {"priority": 2, "channel": "Email", "conditions": {"utm_source_in": ["email", "e-mail", "e_mail", "newsletter"]}},
    {"priority": 3, "channel": "Paid", "conditions": {"utm_medium_in": ["cpc", "ppc", "paid", "paidsearch"]}},
    {"priority": 4, "channel": "Organic Social", "conditions": {"utm_medium_in": ["social", "social-network", "social-media"]}},
    {"priority": 5, "channel": "Organic Social", "conditions": {"referrer_domain_in": ["linkedin.com", "lnkd.in", "github.com", "twitter.com", "x.com", "t.co", "facebook.com", "instagram.com", "youtube.com", "reddit.com", "medium.com"]}},
    {"priority": 6, "channel": "Organic Search", "conditions": {"utm_medium_in": ["organic"]}},
    {"priority": 7, "channel": "Organic Search", "conditions": {"referrer_domain_regex": "(^|\\.)(google|bing|duckduckgo|yahoo|ecosia|baidu|yandex|brave)\\."}},
    {"priority": 8, "channel": "Referral", "conditions": {"referrer_present": True, "referrer_domain_not_in": ["cjhirashi.com"]}},
    {"priority": 9, "channel": "Direct", "conditions": {"no_referrer": True, "no_utm": True}},
    {"priority": 10, "channel": "Unknown", "conditions": {}},
]


@pytest.mark.requisito("RF-009")
def test_classify_channel_application_precedence():
    """utm_medium=postulacion takes precedence over referrer linkedin."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="linkedin.com",
        utm_source=None,
        utm_medium="postulacion",
        own_domains=[],
    )
    assert channel == "Application"


@pytest.mark.requisito("RF-009")
def test_classify_channel_email_medium():
    """utm_medium=email classifies as Email."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium="email",
        own_domains=[],
    )
    assert channel == "Email"


@pytest.mark.requisito("RF-009")
def test_classify_channel_email_source():
    """utm_source=newsletter classifies as Email."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source="newsletter",
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Email"


@pytest.mark.requisito("RF-009")
def test_classify_channel_paid():
    """utm_medium=cpc classifies as Paid."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium="cpc",
        own_domains=[],
    )
    assert channel == "Paid"


@pytest.mark.requisito("RF-009")
def test_classify_channel_organic_social_medium():
    """utm_medium=social classifies as Organic Social."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium="social",
        own_domains=[],
    )
    assert channel == "Organic Social"


@pytest.mark.requisito("RF-009")
def test_classify_channel_organic_social_referrer_lnkd():
    """Referrer lnkd.in classifies as Organic Social."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="lnkd.in",
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Organic Social"


@pytest.mark.requisito("RF-009")
def test_classify_channel_organic_search_medium():
    """utm_medium=organic classifies as Organic Search."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium="organic",
        own_domains=[],
    )
    assert channel == "Organic Search"


@pytest.mark.requisito("RF-009")
def test_classify_channel_organic_search_referrer_google():
    """Referrer www.google.com.mx classifies as Organic Search."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="www.google.com.mx",
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Organic Search"


@pytest.mark.requisito("RF-009")
def test_classify_channel_referral():
    """Referrer blog.example.org (not in own_domains) classifies as Referral."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="blog.example.org",
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Referral"


@pytest.mark.requisito("RF-009")
def test_classify_channel_direct():
    """No referrer + no UTM classifies as Direct."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Direct"


@pytest.mark.requisito("RF-009")
def test_classify_channel_internal_navigation():
    """Referrer cjhirashi.com with own_domains ['cjhirashi.com'] treats as Direct."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="cjhirashi.com",
        utm_source=None,
        utm_medium=None,
        own_domains=["cjhirashi.com"],
    )
    assert channel == "Direct"


@pytest.mark.requisito("RF-009")
def test_classify_channel_unknown_utm_source():
    """utm_source=boletin (not in any rule) without referrer remains Unknown."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source="boletin",
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Unknown"


@pytest.mark.requisito("RF-009")
def test_classify_channel_unknown_condition_key():
    """Unknown condition key in rule => rule doesn't match."""
    rules = [
        {"priority": 0, "channel": "Test", "conditions": {"unknown_key": "value"}},
        {"priority": 1, "channel": "Default", "conditions": {}},
    ]
    channel = classify_channel(
        rules,
        referrer_domain=None,
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Default"


@pytest.mark.requisito("RF-009")
def test_classify_channel_case_insensitive():
    """UTM parameters are case-insensitive."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain=None,
        utm_source=None,
        utm_medium="EMAIL",
        own_domains=[],
    )
    assert channel == "Email"


@pytest.mark.requisito("RF-009")
def test_classify_channel_subdomain():
    """Referrer subdomain of own_domains is treated as internal."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="blog.cjhirashi.com",
        utm_source=None,
        utm_medium=None,
        own_domains=["cjhirashi.com"],
    )
    assert channel == "Direct"


@pytest.mark.requisito("RF-009")
def test_classify_channel_referrer_domain_regex_case_insensitive():
    """referrer_domain_regex matches case-insensitively."""
    channel = classify_channel(
        SEED_RULES,
        referrer_domain="GOOGLE.COM",
        utm_source=None,
        utm_medium=None,
        own_domains=[],
    )
    assert channel == "Organic Search"
