"""
LinkedIn integration service - OAuth (Share on LinkedIn + Sign In with
LinkedIn using OpenID Connect, both self-serve) and the Posts API.

Self-serve LinkedIn apps do not receive a refresh token (that requires
Marketing Developer Platform partner approval), so the access token simply
expires after ~60 days and the user re-runs the Connect flow - there is no
silent renewal to implement here.

The OAuth `state` param carries the authenticated user's id (signed with the
same JWT secret already used for login tokens) rather than relying on a
server-side session, because the callback is a plain browser redirect from
LinkedIn with no Authorization header to identify the user with.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt

from config import settings

logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
IMAGES_URL = "https://api.linkedin.com/rest/images"

# LinkedIn's versioned REST APIs require this header (YYYYMM). LinkedIn
# supports versions up to ~12 months old, so this only needs bumping
# occasionally - it isn't tied to any specific new feature.
LINKEDIN_API_VERSION = "202601"

OAUTH_SCOPES = "openid profile email w_member_social"

STATE_TOKEN_TYPE = "linkedin_oauth_state"
STATE_TOKEN_TTL_MINUTES = 10


class LinkedInError(Exception):
    """Raised when LinkedIn's API rejects a request (bad/expired token, etc.)."""


# ============================================================================
# OAuth
# ============================================================================

def build_state_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "type": STATE_TOKEN_TYPE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=STATE_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_state_token(state: str) -> int:
    """Returns the user_id encoded in a Connect-flow state token, or raises LinkedInError."""
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError as e:
        raise LinkedInError(f"Invalid or expired state: {e}") from e

    if payload.get("type") != STATE_TOKEN_TYPE:
        raise LinkedInError("State token is not a LinkedIn OAuth state token")

    return int(payload["sub"])


def build_authorize_url(user_id: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": build_state_token(user_id),
        "scope": OAUTH_SCOPES,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    """Returns {"access_token": str, "expires_in": int} - no refresh_token, see module docstring."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code != 200:
        logger.error(f"LinkedIn token exchange failed: {response.status_code} {response.text}")
        raise LinkedInError(f"LinkedIn rejected the authorization code ({response.status_code})")
    return response.json()


# ============================================================================
# Llamadas a la API
# ============================================================================

async def fetch_userinfo(access_token: str) -> dict:
    """Returns the OIDC claims: sub, name, email, picture, ..."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code != 200:
        logger.error(f"LinkedIn userinfo failed: {response.status_code} {response.text}")
        raise LinkedInError(f"Could not fetch the LinkedIn profile ({response.status_code})")
    return response.json()


def _linkedin_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
    }


async def upload_image(access_token: str, member_sub: str, image_bytes: bytes) -> str:
    """Uploads an image to LinkedIn's own storage (required before it can be
    referenced in a post - LinkedIn does not accept external image URLs).
    Returns the image's URN (urn:li:image:...)."""
    async with httpx.AsyncClient() as client:
        init_response = await client.post(
            f"{IMAGES_URL}?action=initializeUpload",
            json={"initializeUploadRequest": {"owner": f"urn:li:person:{member_sub}"}},
            headers=_linkedin_headers(access_token),
        )
        if init_response.status_code != 200:
            logger.error(f"LinkedIn image init failed: {init_response.status_code} {init_response.text}")
            raise LinkedInError(f"LinkedIn rejected the image upload ({init_response.status_code})")

        value = init_response.json()["value"]
        upload_url = value["uploadUrl"]
        image_urn = value["image"]

        upload_response = await client.put(
            upload_url,
            content=image_bytes,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if upload_response.status_code not in (200, 201):
            logger.error(f"LinkedIn image binary upload failed: {upload_response.status_code}")
            raise LinkedInError(f"LinkedIn rejected the image bytes ({upload_response.status_code})")

    return image_urn


# ============================================================================
# Publicación de posts
# ============================================================================

async def create_post(
    access_token: str, member_sub: str, text: str, image_urn: Optional[str] = None
) -> Optional[str]:
    """Publishes a post (text, optionally with one image) as the connected
    member. Returns the post's URN if LinkedIn returns one."""
    payload = {
        "author": f"urn:li:person:{member_sub}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if image_urn:
        payload["content"] = {"media": {"id": image_urn}}

    async with httpx.AsyncClient() as client:
        response = await client.post(POSTS_URL, json=payload, headers=_linkedin_headers(access_token))

    if response.status_code != 201:
        logger.error(f"LinkedIn post creation failed: {response.status_code} {response.text}")
        raise LinkedInError(f"LinkedIn rejected the post ({response.status_code}): {response.text}")

    return response.headers.get("x-restli-id") or response.headers.get("x-linkedin-id")
