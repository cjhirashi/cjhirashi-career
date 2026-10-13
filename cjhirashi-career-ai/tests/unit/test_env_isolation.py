"""Aislamiento de los tests: ningún `.env` ni credencial heredada puede llegar a `Settings`."""
import os

import pytest

pytestmark = pytest.mark.requisito("RNF-001")


def _env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("AWS_ACCESS_KEY_ID=FAKEFROMENV\nBEDROCK_REGION=mars-1\n", encoding="utf-8")
    return f


def test_settings_does_not_read_dotenv_from_cwd(tmp_path, monkeypatch):
    from config import Settings

    _env_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    s = Settings()
    assert s.AWS_ACCESS_KEY_ID == ""
    assert s.BEDROCK_REGION == "us-east-1"


def test_settings_does_not_read_an_explicit_dotenv_either(tmp_path):
    from config import Settings

    s = Settings(_env_file=str(_env_file(tmp_path)))
    assert s.AWS_ACCESS_KEY_ID == ""


def test_inherited_aws_and_bedrock_variables_are_scrubbed():
    leaked = [k for k in os.environ if k.startswith(("AWS_", "BEDROCK_"))]
    assert leaked == []


def test_boto3_client_cache_is_empty_at_test_start():
    from providers.bedrock import client

    assert client._clients == {}


def test_singleton_settings_has_no_credentials():
    import config

    assert config.settings.AWS_ACCESS_KEY_ID == "" and config.settings.AWS_SECRET_ACCESS_KEY == ""
