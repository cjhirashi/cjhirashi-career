"""
Geografía de una visita, solo desde las cabeceras `cf-*` que Cloudflare añade
(Managed Transform «Add visitor location headers»). No hay respaldo por IP ni
servicio externo: sin cabeceras la visita queda sin ubicación, y la IP nunca se
usa ni se guarda (RF-005).
"""
from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass
class GeoInfo:
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str] = None


# Mapping of ISO-2 country codes to country names
# Covers ~40 most probable countries in web traffic
COUNTRY_NAMES = {
    "MX": "Mexico",
    "US": "United States",
    "CA": "Canada",
    "ES": "Spain",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "NL": "The Netherlands",
    "BR": "Brazil",
    "AR": "Argentina",
    "CO": "Colombia",
    "CL": "Chile",
    "PE": "Peru",
    "CN": "China",
    "HK": "Hong Kong",
    "SG": "Singapore",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "RU": "Russia",
    "UA": "Ukraine",
    "PL": "Poland",
    "PT": "Portugal",
    "IE": "Ireland",
    "SE": "Sweden",
    "NO": "Norway",
    "FI": "Finland",
    "DK": "Denmark",
    "CH": "Switzerland",
    "AT": "Austria",
    "BE": "Belgium",
    "AU": "Australia",
    "NZ": "New Zealand",
    "ZA": "South Africa",
    "TR": "Turkey",
    "AE": "United Arab Emirates",
    "IL": "Israel",
    "PK": "Pakistan",
    "ID": "Indonesia",
    "VN": "Vietnam",
    "TW": "Taiwan",
    "PH": "Philippines",
    "TH": "Thailand",
}


def geo_from_headers(headers: Mapping[str, str]) -> Optional[GeoInfo]:
    """
    Extract geographic information from Cloudflare headers.

    Reads cf-ipcountry, cf-ipcity, cf-region, cf-iplatitude, cf-iplongitude,
    cf-timezone headers (case-insensitive). Returns None if cf-ipcountry is
    missing, "XX", or "T1".

    Country name is resolved from COUNTRY_NAMES dict, falling back to the ISO code.

    Args:
        headers: HTTP headers mapping (keys are case-insensitive)

    Returns:
        GeoInfo with country name and coordinates, or None
    """
    # Create lowercase header lookup for case-insensitive search
    headers_lower = {k.lower(): v for k, v in headers.items()}

    # Get country code
    country_code = headers_lower.get("cf-ipcountry")
    if not country_code or country_code.strip().upper() in ("XX", "T1"):
        return None

    # Resolve country name
    country_name = COUNTRY_NAMES.get(country_code.upper(), country_code.upper())

    # Get other fields
    region = headers_lower.get("cf-region")
    city = headers_lower.get("cf-ipcity")
    timezone = headers_lower.get("cf-timezone")

    # Parse coordinates
    latitude = None
    longitude = None
    try:
        lat_str = headers_lower.get("cf-iplatitude")
        if lat_str:
            latitude = float(lat_str)
    except (ValueError, TypeError):
        pass

    try:
        lon_str = headers_lower.get("cf-iplongitude")
        if lon_str:
            longitude = float(lon_str)
    except (ValueError, TypeError):
        pass

    return GeoInfo(
        country=country_name,
        region=region,
        city=city,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
