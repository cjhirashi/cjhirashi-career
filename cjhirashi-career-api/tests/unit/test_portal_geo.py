"""
Tests for portal_geo service.
"""
import pytest

from services.portal_geo import geo_from_headers
from services import portal_geo


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
def test_geo_comes_only_from_cloudflare_headers_and_never_from_the_ip():
    """Sin cabeceras no hay geografía: ya no existe respaldo por IP ni servicio externo."""
    assert geo_from_headers({}) is None
    assert geo_from_headers({"cf-ipcountry": "XX"}) is None
    assert geo_from_headers({"cf-ipcountry": "MX", "cf-ipcity": "Celaya"}).city == "Celaya"


@pytest.mark.requisito("RF-004")
def test_external_ip_lookup_service_is_retired():
    import importlib.util

    from config import settings

    assert importlib.util.find_spec("services.geo_ip_service") is None
    assert not hasattr(settings, "GEO_SOURCE")
    assert not hasattr(portal_geo, "resolve_request_geo")
