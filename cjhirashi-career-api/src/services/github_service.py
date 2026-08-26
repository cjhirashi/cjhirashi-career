"""
Cliente GitHub REST (lectura).

Sin token: repos públicos de un username (admin panel y fallback del L3).
Con GITHUB_TOKEN: usuario autenticado, repos privados, archivos y search/code.
El L3 agent_github no escribe (no crea issues, PRs ni pushes).
"""
from __future__ import annotations

import base64
import logging
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.github_profile import GitHubProfile

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
REPOS_URL = "https://api.github.com/users/{username}/repos"
_USER_AGENT = "Portafolio-cjhirashi (github-agent)"
_TIMEOUT = 15.0
_MAX_FILE_CHARS = 12_000


class GitHubError(Exception):
    pass


def _token() -> str:
    return (settings.GITHUB_TOKEN or "").strip()


def _headers(token: Optional[str] = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": _USER_AGENT,
    }
    auth = token if token is not None else _token()
    if auth:
        headers["Authorization"] = f"Bearer {auth}"
    return headers


def split_owner_repo(owner: Optional[str], repo: str) -> tuple[str, str]:
    value = (repo or "").strip().removesuffix(".git")
    if "/" in value and not (owner or "").strip():
        left, right = value.split("/", 1)
        return left.strip(), right.strip()
    return (owner or "").strip(), value


def _summarize_repo(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": repo.get("full_name"),
        "name": repo.get("name"),
        "description": repo.get("description"),
        "url": repo.get("html_url"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "updated_at": repo.get("updated_at"),
        "default_branch": repo.get("default_branch"),
        "private": bool(repo.get("private")),
        "is_fork": bool(repo.get("fork")),
        "topics": repo.get("topics") or [],
    }


async def _request(method: str, path: str, *, params: Optional[dict[str, Any]] = None) -> httpx.Response:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.request(method, url, params=params, headers=_headers())
    return response


def _raise_for_status(response: httpx.Response, not_found: str) -> None:
    if response.status_code == 404:
        raise GitHubError(not_found)
    if response.status_code == 401:
        raise GitHubError("Token de GitHub inválido o expirado")
    if response.status_code == 403:
        raise GitHubError("GitHub rechazó la petición (permisos o rate limit)")
    if response.status_code != 200:
        logger.error("GitHub %s %s", response.status_code, response.text[:300])
        raise GitHubError(f"GitHub respondió con un error ({response.status_code})")


# ============================================================================
# Listado de repositorios públicos (Admin Panel, sin token)
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


# ============================================================================
# Conexión y consultas autenticadas (L3 agent_github)
# ============================================================================

async def connection_status() -> dict[str, Any]:
    token = _token()
    if not token:
        return {"connected": False, "reason": "GITHUB_TOKEN no configurado"}
    response = await _request("GET", "/user")
    if response.status_code == 401:
        return {"connected": False, "reason": "token inválido o expirado"}
    if response.status_code != 200:
        return {"connected": False, "reason": f"GitHub respondió {response.status_code}"}
    user = response.json()
    return {
        "connected": True,
        "login": user.get("login"),
        "name": user.get("name"),
        "html_url": user.get("html_url"),
        "public_repos": user.get("public_repos"),
        "total_private_repos": user.get("total_private_repos"),
        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
        "scopes": response.headers.get("X-OAuth-Scopes") or "",
    }


async def profile_username(db: AsyncSession, user_id: str) -> Optional[str]:
    result = await db.execute(select(GitHubProfile).where(GitHubProfile.user_id == user_id))
    row = result.scalar_one_or_none()
    username = (row.username or "").strip() if row else ""
    return username or None


async def resolve_owner(db: AsyncSession, user_id: str, owner: Optional[str] = None) -> dict[str, Any]:
    explicit = (owner or "").strip()
    if explicit:
        return {"owner": explicit, "source": "argument"}
    status = await connection_status()
    if status.get("connected") and status.get("login"):
        return {"owner": status["login"], "source": "token"}
    username = await profile_username(db, user_id)
    if username:
        return {"owner": username, "source": "github-profile"}
    return {
        "error": (
            "No hay dueño de GitHub: configura GITHUB_TOKEN o el username en github-profile."
        )
    }


async def list_repos(
    db: AsyncSession,
    user_id: str,
    *,
    owner: Optional[str] = None,
    query: Optional[str] = None,
    per_page: int = 30,
) -> dict[str, Any]:
    resolved = await resolve_owner(db, user_id, owner)
    if resolved.get("error"):
        return resolved
    login = resolved["owner"]
    limit = max(1, min(int(per_page or 30), 50))
    token = _token()
    needle = (query or "").strip().lower()
    use_auth = False
    if token:
        status = await connection_status()
        auth_login = (status.get("login") or "") if status.get("connected") else ""
        use_auth = bool(auth_login) and login.lower() == auth_login.lower()
    if use_auth:
        response = await _request(
            "GET",
            "/user/repos",
            params={"sort": "updated", "per_page": limit, "affiliation": "owner,collaborator"},
        )
        _raise_for_status(response, "No se encontraron repositorios")
        rows = [_summarize_repo(r) for r in response.json()]
    else:
        try:
            rows = await list_public_repos(login)
        except GitHubError as exc:
            return {"error": str(exc)}
        rows = rows[:limit]
    if needle:
        rows = [
            r
            for r in rows
            if needle in (r.get("name") or "").lower()
            or needle in (r.get("full_name") or "").lower()
            or needle in (r.get("description") or "").lower()
        ]
    return {"owner": login, "source": resolved["source"], "items": rows}


async def get_repo(owner: str, repo: str) -> dict[str, Any]:
    owner, repo = split_owner_repo(owner, repo)
    if not owner or not repo:
        return {"error": "owner y repo son obligatorios (ej. cjhirashi/portafolio)"}
    response = await _request("GET", f"/repos/{owner}/{repo}")
    try:
        _raise_for_status(response, f"No existe {owner}/{repo}")
    except GitHubError as exc:
        return {"error": str(exc)}
    data = response.json()
    summary = _summarize_repo(data)
    summary["homepage"] = data.get("homepage")
    summary["license"] = (data.get("license") or {}).get("spdx_id")
    summary["open_issues"] = data.get("open_issues_count")
    summary["pushed_at"] = data.get("pushed_at")
    return {"item": summary}


async def list_contents(owner: str, repo: str, path: str = "", ref: Optional[str] = None) -> dict[str, Any]:
    owner, repo = split_owner_repo(owner, repo)
    if not owner or not repo:
        return {"error": "owner y repo son obligatorios"}
    suffix = (path or "").strip().lstrip("/")
    api_path = f"/repos/{owner}/{repo}/contents/{suffix}" if suffix else f"/repos/{owner}/{repo}/contents"
    params = {"ref": ref} if ref else None
    response = await _request("GET", api_path, params=params)
    try:
        _raise_for_status(response, f"No existe {owner}/{repo}:{suffix or '/'}")
    except GitHubError as exc:
        return {"error": str(exc)}
    payload = response.json()
    if isinstance(payload, dict):
        return {
            "kind": "file",
            "item": {
                "name": payload.get("name"),
                "path": payload.get("path"),
                "type": payload.get("type"),
                "size": payload.get("size"),
                "url": payload.get("html_url"),
            },
        }
    items = [
        {
            "name": row.get("name"),
            "path": row.get("path"),
            "type": row.get("type"),
            "size": row.get("size"),
            "url": row.get("html_url"),
        }
        for row in payload
    ]
    return {"kind": "dir", "path": suffix or "/", "items": items}


async def get_file(owner: str, repo: str, path: str, ref: Optional[str] = None) -> dict[str, Any]:
    owner, repo = split_owner_repo(owner, repo)
    file_path = (path or "").strip().lstrip("/")
    if not owner or not repo or not file_path:
        return {"error": "owner, repo y path son obligatorios"}
    params = {"ref": ref} if ref else None
    response = await _request("GET", f"/repos/{owner}/{repo}/contents/{file_path}", params=params)
    try:
        _raise_for_status(response, f"No existe {owner}/{repo}/{file_path}")
    except GitHubError as exc:
        return {"error": str(exc)}
    payload = response.json()
    if isinstance(payload, list) or payload.get("type") != "file":
        return {"error": "path apunta a un directorio; usa list_github_contents"}
    encoding = payload.get("encoding")
    raw = payload.get("content") or ""
    if encoding == "base64":
        try:
            decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
        except (ValueError, UnicodeDecodeError):
            return {"error": "No se pudo decodificar el archivo como texto"}
    else:
        decoded = str(raw)
    truncated = len(decoded) > _MAX_FILE_CHARS
    if truncated:
        decoded = decoded[:_MAX_FILE_CHARS] + "…"
    return {
        "name": payload.get("name"),
        "path": payload.get("path"),
        "sha": payload.get("sha"),
        "size": payload.get("size"),
        "url": payload.get("html_url"),
        "truncated": truncated,
        "content": decoded,
    }


async def search_code(query: str, *, owner: Optional[str] = None, repo: Optional[str] = None) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"error": "query required"}
    if not _token():
        return {"error": "search_github_code requiere GITHUB_TOKEN"}
    parts = [q]
    owner, repo_name = split_owner_repo(owner, repo or "")
    if owner and repo_name:
        parts.append(f"repo:{owner}/{repo_name}")
    elif owner:
        parts.append(f"user:{owner}")
    response = await _request("GET", "/search/code", params={"q": " ".join(parts), "per_page": 10})
    try:
        _raise_for_status(response, "Sin resultados")
    except GitHubError as exc:
        return {"error": str(exc)}
    payload = response.json()
    items = [
        {
            "name": row.get("name"),
            "path": row.get("path"),
            "repo": (row.get("repository") or {}).get("full_name"),
            "url": row.get("html_url"),
        }
        for row in payload.get("items") or []
    ]
    return {"total_count": payload.get("total_count", len(items)), "items": items}
