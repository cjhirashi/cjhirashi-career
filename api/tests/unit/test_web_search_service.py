"""SSRF y parsers de consulta web (sin red)."""
import pytest

from services.web_search_service import (
    WebSearchError,
    assert_public_http_url,
    html_to_text,
    parse_brave_payload,
    parse_ddg_html,
    unwrap_ddg_href,
)


def test_ssrf_blocks_localhost_and_private_ips():
    for url in (
        "http://localhost/admin",
        "http://127.0.0.1/",
        "http://10.0.0.1/secret",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "ftp://example.com/file",
    ):
        with pytest.raises(WebSearchError):
            assert_public_http_url(url)


def test_ssrf_blocks_embedded_credentials():
    with pytest.raises(WebSearchError):
        assert_public_http_url("https://user:pass@example.com/")


def test_unwrap_ddg_and_parse_html():
    href = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage"
    assert unwrap_ddg_href(href) == "https://example.com/page"
    html = """
    <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org">Python</a>
    <a class="result__snippet">Lenguaje</a>
    """
    items = parse_ddg_html(html, 5)
    assert items[0]["url"] == "https://docs.python.org"
    assert items[0]["title"] == "Python"
    assert "Lenguaje" in items[0]["snippet"]


def test_parse_brave_payload():
    payload = {"web": {"results": [{"title": "T", "url": "https://ex.com", "description": "D"}]}}
    items = parse_brave_payload(payload, 8)
    assert items == [{"title": "T", "url": "https://ex.com", "snippet": "D"}]


def test_html_to_text_strips_script():
    text = html_to_text("<html><script>alert(1)</script><p>Hola <b>mundo</b></p></html>")
    assert "alert" not in text
    assert "Hola" in text
    assert "mundo" in text
