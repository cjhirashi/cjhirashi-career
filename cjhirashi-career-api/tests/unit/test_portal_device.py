"""
Tests for portal_device service.
"""
import pytest

from services.portal_device import parse_device


@pytest.mark.requisito("RF-006")
def test_parse_device_chrome_windows():
    """Chrome on Windows."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    result = parse_device(ua, accept_language="en-US", screen="1920x1080")

    assert result["device_type"] == "desktop"
    assert result["browser"] == "Chrome"
    assert result["browser_version"] == "125.0"
    assert result["os"] == "Windows"
    assert result["os_version"] == "10"
    assert result["screen_size"] == "1920x1080"
    assert result["language"] == "en-US"


@pytest.mark.requisito("RF-006")
def test_parse_device_safari_iphone():
    """Safari on iPhone."""
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    result = parse_device(ua, accept_language="en-US")

    assert result["device_type"] == "mobile"
    assert result["os"] == "iOS"
    assert result["language"] == "en-US"


@pytest.mark.requisito("RF-006")
def test_parse_device_safari_ipad():
    """Safari on iPad."""
    ua = "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    result = parse_device(ua)

    assert result["device_type"] == "tablet"
    assert result["os"] == "iOS"


@pytest.mark.requisito("RF-006")
def test_parse_device_chrome_android_mobile():
    """Chrome on Android Mobile."""
    ua = "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36"
    result = parse_device(ua)

    assert result["device_type"] == "mobile"
    assert result["os"] == "Android"


@pytest.mark.requisito("RF-006")
def test_parse_device_chrome_android_tablet():
    """Chrome on Android Tablet (no Mobile in UA)."""
    ua = "Mozilla/5.0 (Linux; Android 11; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    result = parse_device(ua)

    assert result["device_type"] == "tablet"
    assert result["os"] == "Android"


@pytest.mark.requisito("RF-006")
def test_parse_device_firefox_linux():
    """Firefox on Linux."""
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    result = parse_device(ua)

    assert result["device_type"] == "desktop"
    assert result["browser"] == "Firefox"
    assert result["os"] == "Linux"


@pytest.mark.requisito("RF-006")
def test_parse_device_googlebot():
    """Googlebot."""
    ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
    result = parse_device(ua)

    assert result["device_type"] == "bot"


@pytest.mark.requisito("RF-006")
def test_parse_device_empty_ua():
    """Empty user agent."""
    result = parse_device("")

    assert result["device_type"] == "unknown"
    assert result["browser"] is None
    assert result["os"] is None


@pytest.mark.requisito("RF-006")
def test_parse_device_none_ua():
    """None user agent."""
    result = parse_device(None)

    assert result["device_type"] == "unknown"
    assert result["browser"] is None
    assert result["os"] is None


@pytest.mark.requisito("RF-006")
def test_parse_device_language_parsing():
    """Language header parsing."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"
    result = parse_device(ua, accept_language="es-MX,es;q=0.9,en;q=0.8")

    assert result["language"] == "es-MX"


@pytest.mark.requisito("RF-006")
def test_parse_device_language_none():
    """No language header."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"
    result = parse_device(ua, accept_language=None)

    assert result["language"] is None


@pytest.mark.requisito("RF-006")
def test_parse_device_screen_none():
    """No screen info."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"
    result = parse_device(ua, screen=None)

    assert result["screen_size"] is None


@pytest.mark.requisito("RF-006")
def test_parse_device_always_returns_dict():
    """parse_device always returns a dict with all expected keys."""
    for ua in [None, "", "invalid", "Chrome/1.0"]:
        result = parse_device(ua)
        assert isinstance(result, dict)
        assert "device_type" in result
        assert "browser" in result
        assert "browser_version" in result
        assert "os" in result
        assert "os_version" in result
        assert "screen_size" in result
        assert "language" in result
