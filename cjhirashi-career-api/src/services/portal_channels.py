"""
Portal channels classification service.

Classifies traffic sources into predefined channels (Direct, Organic Search,
Organic Social, Email, Referral, Paid, Application, Unknown) based on UTM
parameters and referrer domain.
"""
import re
from typing import Optional


def extract_domain(url: str | None) -> str | None:
    """
    Extract domain from a URL.

    Returns the domain in lowercase, without scheme, port, path, or 'www.' prefix.
    Returns None if the URL is empty or invalid.

    Args:
        url: Full URL or domain string

    Returns:
        Normalized domain (lowercase, no scheme/port/path/www), or None
    """
    if not url:
        return None

    url = url.strip()
    if not url:
        return None

    # Remove scheme if present
    if "://" in url:
        url = url.split("://", 1)[1]

    # Remove path if present
    if "/" in url:
        url = url.split("/", 1)[0]

    # Remove port if present
    if ":" in url:
        url = url.rsplit(":", 1)[0]

    # Remove www. prefix
    if url.lower().startswith("www."):
        url = url[4:]

    # Normalize to lowercase
    url = url.lower()

    # Validate it's not empty
    if not url:
        return None

    return url


def classify_channel(
    rules: list[dict],
    *,
    referrer_domain: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    own_domains: list[str],
) -> str:
    """
    Classify traffic source into a channel based on rules.

    Evaluates rules in priority order (ascending). Returns the channel name of
    the first rule whose conditions all match. If no rule matches, returns "Unknown".

    Conditions are AND-ed: ALL must be true for a rule to match.
    Unknown condition keys cause the rule to NOT match (never raises).

    If referrer_domain matches own_domains (exact or subdomain), it's treated as
    no referrer (internal navigation).

    Supported condition keys:
    - utm_medium_in: list; matches if utm_medium (normalized) is in the list
    - utm_source_in: list; matches if utm_source (normalized) is in the list
    - referrer_domain_in: list; matches if referrer_domain equals or is subdomain of a domain
    - referrer_domain_not_in: list; inverse of referrer_domain_in
    - referrer_domain_regex: string; matches if re.search(regex, referrer_domain, re.I)
    - referrer_present: bool; matches if (has referrer) == value
    - no_referrer: bool; matches if (no referrer) == value
    - no_utm: bool; matches if (both utm_source and utm_medium are empty) == value

    Args:
        rules: List of {"priority": int, "channel": str, "conditions": dict}
        referrer_domain: Domain that referred this visit (or None)
        utm_source: UTM source parameter (or None)
        utm_medium: UTM medium parameter (or None)
        own_domains: List of domains to treat as internal

    Returns:
        Channel name (str)
    """
    # Normalize own_domains to lowercase
    own_domains_lower = [d.lower() for d in own_domains] if own_domains else []

    # Check if referrer is internal (owned domain)
    if referrer_domain:
        referrer_lower = referrer_domain.lower()
        is_internal = any(
            referrer_lower == own_domain or referrer_lower.endswith("." + own_domain)
            for own_domain in own_domains_lower
        )
        if is_internal:
            referrer_domain = None

    # Normalize UTM parameters
    utm_source_normalized = utm_source.lower().strip() if utm_source else None
    utm_medium_normalized = utm_medium.lower().strip() if utm_medium else None

    # Sort rules by priority
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 999))

    for rule in sorted_rules:
        conditions = rule.get("conditions", {})

        # Empty conditions always match
        if not conditions:
            return rule.get("channel", "Unknown")

        # Check all conditions (AND)
        all_match = True
        for key, value in conditions.items():
            if key == "utm_medium_in":
                if not isinstance(value, list):
                    all_match = False
                    break
                if utm_medium_normalized not in value:
                    all_match = False
                    break
            elif key == "utm_source_in":
                if not isinstance(value, list):
                    all_match = False
                    break
                if utm_source_normalized not in value:
                    all_match = False
                    break
            elif key == "referrer_domain_in":
                if not isinstance(value, list):
                    all_match = False
                    break
                referrer_lower = referrer_domain.lower() if referrer_domain else None
                found = False
                for domain in value:
                    domain_lower = domain.lower()
                    if referrer_lower and (
                        referrer_lower == domain_lower or
                        referrer_lower.endswith("." + domain_lower)
                    ):
                        found = True
                        break
                if not found:
                    all_match = False
                    break
            elif key == "referrer_domain_not_in":
                if not isinstance(value, list):
                    all_match = False
                    break
                referrer_lower = referrer_domain.lower() if referrer_domain else None
                found = False
                for domain in value:
                    domain_lower = domain.lower()
                    if referrer_lower and (
                        referrer_lower == domain_lower or
                        referrer_lower.endswith("." + domain_lower)
                    ):
                        found = True
                        break
                if found:
                    all_match = False
                    break
            elif key == "referrer_domain_regex":
                if not isinstance(value, str):
                    all_match = False
                    break
                if not referrer_domain:
                    all_match = False
                    break
                try:
                    if not re.search(value, referrer_domain, re.IGNORECASE):
                        all_match = False
                        break
                except re.error:
                    all_match = False
                    break
            elif key == "referrer_present":
                if (referrer_domain is not None) != value:
                    all_match = False
                    break
            elif key == "no_referrer":
                if (referrer_domain is None) != value:
                    all_match = False
                    break
            elif key == "no_utm":
                has_utm = utm_source_normalized is not None or utm_medium_normalized is not None
                if has_utm == value:
                    all_match = False
                    break
            else:
                # Unknown condition key => rule doesn't match
                all_match = False
                break

        if all_match:
            return rule.get("channel", "Unknown")

    return "Unknown"
