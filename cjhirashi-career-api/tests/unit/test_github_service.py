"""GitHub agent client — conexión y search sin red."""
from unittest.mock import patch

import pytest

from services import github_service


def test_split_owner_repo():
    assert github_service.split_owner_repo(None, "cjhirashi/portafolio") == ("cjhirashi", "portafolio")
    assert github_service.split_owner_repo("cjhirashi", "portafolio") == ("cjhirashi", "portafolio")
    assert github_service.split_owner_repo("", "acme/app.git") == ("acme", "app")


@pytest.mark.asyncio
async def test_connection_status_without_token():
    with patch.object(github_service, "_token", return_value=""):
        status = await github_service.connection_status()
    assert status["connected"] is False
    assert "GITHUB_TOKEN" in status["reason"]


@pytest.mark.asyncio
async def test_search_code_requires_token():
    with patch.object(github_service, "_token", return_value=""):
        result = await github_service.search_code("def login")
    assert "error" in result
    assert "GITHUB_TOKEN" in result["error"]
