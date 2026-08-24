"""
GitHub public API client - just enough to list a username's public repos
for display in the admin panel. GitHub's REST API serves public repo data
with no authentication required, so unlike LinkedIn there's no OAuth app,
no partner approval, nothing to configure - just the username.
Unauthenticated requests are capped at 60/hour per IP, which is more than
enough for an admin panel a single person refreshes occasionally.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

REPOS_URL = "https://api.github.com/users/{username}/repos"


class GitHubError(Exception):
    pass


# ============================================================================
# Listado de repositorios
# ============================================================================

async def list_public_repos(username: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            REPOS_URL.format(username=username),
            params={"sort": "updated", "per_page": 30},
            headers={"Accept": "application/vnd.github+json"},
        )

    if response.status_code == 404:
        raise GitHubError(f"No existe el usuario de GitHub '{username}'")
    if response.status_code != 200:
        logger.error(f"GitHub repos fetch failed: {response.status_code} {response.text}")
        raise GitHubError(f"GitHub respondió con un error ({response.status_code})")

    repos = response.json()
    return [
        {
            "name": repo["name"],
            "description": repo.get("description"),
            "url": repo["html_url"],
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "updated_at": repo.get("updated_at"),
            "is_fork": repo.get("fork", False),
            "topics": repo.get("topics", []),
        }
        for repo in repos
        if not repo.get("private")
    ]
