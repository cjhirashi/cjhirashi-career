"""
Tests for portal_geo service.
"""
import pytest
from unittest.mock import AsyncMock, patch

from services.portal_geo import geo_from_headers, resolve_request_geo
from services.geo_ip_service import GeoInfo
from config import settings


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_valid():
    """Extract geo from valid Cloudflare headers."""
    headers = {
        "CF-IPCountry": "MX",
        "CF-IPCity": "Mexico City",
        "CF-Region": "Mexico City",
        "CF-IPLatitude": "19.4326",
        "CF-IPLongitude": "-99.1332",
        "CF-Timezone": "America/Mexico_City",
    }
    result = geo_from_headers(headers)

    assert result is not None
    assert result.country == "Mexico"
    assert result.region == "Mexico City"
    assert result.city == "Mexico City"
    assert result.latitude == 19.4326
    assert result.longitude == -99.1332
    assert result.timezone == "America/Mexico_City"


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_case_insensitive():
    """Headers are matched case-insensitively."""
    headers = {
        "cf-ipcountry": "US",
        "cf-ipcity": "San Francisco",
    }
    result = geo_from_headers(headers)

    assert result is not None
    assert result.country == "United States"
    assert result.city == "San Francisco"


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_missing_country():
    """Missing cf-ipcountry returns None."""
    headers = {
        "cf-ipcity": "San Francisco",
        "cf-timezone": "America/Los_Angeles",
    }
    result = geo_from_headers(headers)

    assert result is None


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_country_xx():
    """Country code 'XX' returns None."""
    headers = {
        "cf-ipcountry": "XX",
    }
    result = geo_from_headers(headers)

    assert result is None


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_country_t1():
    """Country code 'T1' returns None."""
    headers = {
        "cf-ipcountry": "T1",
    }
    result = geo_from_headers(headers)

    assert result is None


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_unknown_country_code():
    """Unknown country code uses ISO code as name."""
    headers = {
        "cf-ipcountry": "ZZ",  # Not in COUNTRY_NAMES dict
    }
    result = geo_from_headers(headers)

    assert result is not None
    assert result.country == "ZZ"


@pytest.mark.requisito("RF-004")
def test_geo_from_headers_invalid_coordinates():
    """Invalid coordinates are handled gracefully."""
    headers = {
        "cf-ipcountry": "MX",
        "cf-iplatitude": "not-a-number",
        "cf-iplongitude": "also-not-a-number",
    }
    result = geo_from_headers(headers)

    assert result is not None
    assert result.country == "Mexico"
    assert result.latitude is None
    assert result.longitude is None


@pytest.mark.requisito("RF-004")
async def test_resolve_request_geo_cf_mode():
    """GEO_SOURCE='cf' uses only Cloudflare headers."""
    headers = {
        "cf-ipcountry": "MX",
        "cf-ipcity": "Mexico City",
    }

    with patch("services.portal_geo.settings") as mock_settings:
        mock_settings.GEO_SOURCE = "cf"
        with patch("services.portal_geo.resolve_geo") as mock_resolve:
            result = await resolve_request_geo(headers, ip="1.2.3.4")

            assert result is not None
            assert result.country == "Mexico"
            # resolve_geo should not be called
            mock_resolve.assert_not_called()


@pytest.mark.requisito("RF-004")
async def test_resolve_request_geo_ipapi_mode():
    """GEO_SOURCE='ipapi' uses only resolve_geo."""
    headers = {
        "cf-ipcountry": "MX",  # Should be ignored
    }

    mock_geo = GeoInfo(
        country="United States",
        region="California",
        city="San Francisco",
        latitude=37.7749,
        longitude=-122.4194,
        timezone="America/Los_Angeles",
    )

    with patch("services.portal_geo.settings") as mock_settings:
        mock_settings.GEO_SOURCE = "ipapi"
        with patch("services.portal_geo.resolve_geo", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = mock_geo
            result = await resolve_request_geo(headers, ip="1.2.3.4")

            assert result is mock_geo
            # resolve_geo should be called
            mock_resolve.assert_called_once_with("1.2.3.4")


@pytest.mark.requisito("RF-004")
async def test_resolve_request_geo_auto_mode_cf_found():
    """GEO_SOURCE='auto' uses CF headers if valid cf-ipcountry."""
    headers = {
        "cf-ipcountry": "MX",
        "cf-ipcity": "Mexico City",
    }

    with patch("services.portal_geo.settings") as mock_settings:
        mock_settings.GEO_SOURCE = "auto"
        with patch("services.portal_geo.resolve_geo") as mock_resolve:
            result = await resolve_request_geo(headers, ip="1.2.3.4")

            assert result is not None
            assert result.country == "Mexico"
            # resolve_geo should not be called
            mock_resolve.assert_not_called()


@pytest.mark.requisito("RF-004")
async def test_resolve_request_geo_auto_mode_cf_not_found():
    """GEO_SOURCE='auto' falls back to resolve_geo if no cf-ipcountry."""
    headers = {}

    mock_geo = GeoInfo(
        country="United States",
        region="California",
        city="San Francisco",
        latitude=37.7749,
        longitude=-122.4194,
        timezone="America/Los_Angeles",
    )

    with patch("services.portal_geo.settings") as mock_settings:
        mock_settings.GEO_SOURCE = "auto"
        with patch("services.portal_geo.resolve_geo", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = mock_geo
            result = await resolve_request_geo(headers, ip="1.2.3.4")

            assert result is mock_geo
            # resolve_geo should be called
            mock_resolve.assert_called_once_with("1.2.3.4")


@pytest.mark.requisito("RF-004")
async def test_resolve_request_geo_never_raises():
    """resolve_request_geo never raises an exception."""
    headers = {"cf-ipcountry": "XX"}  # Invalid

    with patch("services.portal_geo.resolve_geo", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.side_effect = Exception("Network error")
        result = await resolve_request_geo(headers, ip="1.2.3.4")

        # Should return None, not raise
        assert result is None
