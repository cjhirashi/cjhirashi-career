"""
Portal device detection service.

Parses user agent and related headers to extract device, browser, OS, and
language information.
"""
from typing import Optional
from ua_parser import parse

from services.portal_bots import BOT_UA_RE


def parse_device(
    user_agent: str | None,
    *,
    accept_language: str | None = None,
    screen: str | None = None,
) -> dict:
    """
    Parse device information from headers.

    Returns a dict with keys:
    - device_type: 'desktop'|'mobile'|'tablet'|'bot'|'unknown'
    - browser: Browser family (e.g., "Chrome"), or None
    - browser_version: Major.minor version (e.g., "125.0"), or None
    - os: OS family (e.g., "Windows"), or None
    - os_version: Major version, or None
    - screen_size: The screen string passed in, or None
    - language: First language from Accept-Language (e.g., "es-MX"), or None

    Never raises an exception. Handles empty/invalid user agents gracefully.

    Args:
        user_agent: User-Agent header value
        accept_language: Accept-Language header value
        screen: Screen resolution string (e.g., "390x844")

    Returns:
        Dict with device info
    """
    result_dict = {
        "device_type": "unknown",
        "browser": None,
        "browser_version": None,
        "os": None,
        "os_version": None,
        "screen_size": screen,
        "language": None,
    }

    # Parse user agent
    if not user_agent:
        return result_dict

    try:
        result = parse(user_agent)
    except (TypeError, ValueError):
        return result_dict

    # Check if bot
    if BOT_UA_RE.search(user_agent):
        result_dict["device_type"] = "bot"
        return result_dict

    # Extract browser info
    if result.user_agent:
        result_dict["browser"] = result.user_agent.family
        if result.user_agent.major is not None:
            minor = result.user_agent.minor or "0"
            result_dict["browser_version"] = f"{result.user_agent.major}.{minor}"

    # Extract OS info
    if result.os:
        result_dict["os"] = result.os.family
        if result.os.major is not None:
            result_dict["os_version"] = str(result.os.major)

    # Determine device type
    if result.device:
        device_family = result.device.family or ""
        device_family_lower = device_family.lower()

        # iPad is tablet
        if device_family_lower == "ipad":
            result_dict["device_type"] = "tablet"
        # iPhone is mobile
        elif device_family_lower == "iphone":
            result_dict["device_type"] = "mobile"
        # Android: check if it has "Mobile" in UA string
        elif result.os and result.os.family == "Android":
            if "Mobile" in user_agent:
                result_dict["device_type"] = "mobile"
            else:
                result_dict["device_type"] = "tablet"
        else:
            # Everything else is desktop
            result_dict["device_type"] = "desktop"
    else:
        # No device detected => desktop (unless it's empty UA which returns 'unknown')
        result_dict["device_type"] = "desktop"

    # Extract language
    if accept_language:
        # Parse Accept-Language header: e.g., "es-MX,es;q=0.9,en;q=0.8"
        # Take the first language (before comma), without the q parameter
        first_lang = accept_language.split(",")[0].strip()
        if first_lang:
            # Remove q parameter if present (e.g., "es-MX;q=0.9" -> "es-MX")
            if ";" in first_lang:
                first_lang = first_lang.split(";")[0].strip()
            if first_lang:
                result_dict["language"] = first_lang

    return result_dict
