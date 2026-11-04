"""
Portal bot detection service.

Calculates a bot score (0-100) based on behavioral signals and user agent.
Bot scores >= BOT_THRESHOLD (70) are classified as bots.
"""
import re

BOT_THRESHOLD = 70

# Regex to detect bot user agents
BOT_UA_RE = re.compile(
    r"bot|crawl|spider|headless|curl|wget|python|httpclient|scrapy|slurp|"
    r"facebookexternalhit|lighthouse|monitor|preview",
    re.IGNORECASE
)


def score_bot(
    *,
    user_agent: str | None,
    accept_language: str | None,
    has_client_visitor_id: bool,
    finished: bool,
    pageviews: int,
    active_ms: int,
    max_scroll_pct: int,
) -> tuple[int, list[str]]:
    """
    Calculate bot score and reasons.

    Scores are additive (max 100). Returns (score, reasons) where reasons
    are listed in the order they were applied.

    Scoring rules:
    - UA missing/None: +60 "ua_missing"
    - UA matches bot pattern: +80 "ua_bot"
    - No accept_language: +20 "no_language"
    - has_client_visitor_id False: +10 "no_visitor_id"
    - Only if finished=True: pageviews <= 1 AND active_ms < 1000 AND max_scroll_pct == 0: +15 "no_interaction"

    Args:
        user_agent: User-Agent header value
        accept_language: Accept-Language header value
        has_client_visitor_id: Whether client provided a persistent visitor ID
        finished: Whether the visit finished (session ended)
        pageviews: Number of pageviews in visit
        active_ms: Active time in milliseconds
        max_scroll_pct: Maximum scroll percentage reached

    Returns:
        Tuple of (score, reasons) where score is capped at 100
    """
    score = 0
    reasons: list[str] = []

    # UA missing
    if not user_agent:
        score += 60
        reasons.append("ua_missing")
    # UA is bot
    elif BOT_UA_RE.search(user_agent):
        score += 80
        reasons.append("ua_bot")

    # No accept_language
    if not accept_language or not accept_language.strip():
        score += 20
        reasons.append("no_language")

    # No client visitor ID
    if not has_client_visitor_id:
        score += 10
        reasons.append("no_visitor_id")

    # No interaction (only if visit is finished)
    if finished:
        if pageviews <= 1 and active_ms < 1000 and max_scroll_pct == 0:
            score += 15
            reasons.append("no_interaction")

    # Cap at 100
    score = min(score, 100)

    return score, reasons


def is_bot(score: int) -> bool:
    """Check if a bot score indicates a bot."""
    return score >= BOT_THRESHOLD
