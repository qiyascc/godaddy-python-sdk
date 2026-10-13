from __future__ import annotations

import json

import pytest

from godaddy import AuthenticationError, GoDaddy, Settings, load_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in ("API_KEY", "API_SECRET", "ENVIRONMENT", "CONFIG", "TIMEOUT", "MAX_RETRIES", "BASE_URL"):
        monkeypatch.delenv(f"GODADDY_{name}", raising=False)
    monkeypatch.chdir(tmp_path)


def test_credentials_from_env(monkeypatch):
    monkeypatch.setenv("GODADDY_API_KEY", "k")
    monkeypatch.setenv("GODADDY_API_SECRET", "s")
    client = GoDaddy()
    assert client._default_headers()["Authorization"] == "sso-key k:s"
    assert client.base_url == "https://api.godaddy.com"


def test_missing_credentials():
    with pytest.raises(AuthenticationError):
        GoDaddy()


def test_ote_environment():
    assert GoDaddy("k", "s", environment="ote").base_url == "https://api.ote-godaddy.com"


def test_unknown_environment():
    with pytest.raises(ValueError, match="staging"):
        GoDaddy("k", "s", environment="staging")


def test_custom_base_url_and_shopper():
    client = GoDaddy("k", "s", base_url="https://proxy.local/", shopper_id="123")
    assert client.base_url == "https://proxy.local"
    assert client._default_headers()["X-Shopper-Id"] == "123"


def test_env_values_are_typed(monkeypatch):
    monkeypatch.setenv("GODADDY_TIMEOUT", "4.5")
    monkeypatch.setenv("GODADDY_MAX_RETRIES", "9")
    client = GoDaddy("k", "s")
    assert client.timeout == 4.5
    assert client.max_retries == 9


def test_config_file_from_env(monkeypatch, tmp_path):
    path = tmp_path / "custom.json"
    path.write_text(json.dumps({"api_key": "fk", "api_secret": "fs", "environment": "ote", "timeout": 12}))
    monkeypatch.setenv("GODADDY_CONFIG", str(path))
    client = GoDaddy()
    assert client._default_headers()["Authorization"] == "sso-key fk:fs"
    assert client.base_url == "https://api.ote-godaddy.com"
    assert client.timeout == 12


def test_default_toml_file_and_env_priority(monkeypatch, tmp_path):
    (tmp_path / "godaddy.toml").write_text('api_key = "tk"\napi_secret = "ts"\nmax_retries = 1\n')
    monkeypatch.setenv("GODADDY_MAX_RETRIES", "6")
    client = GoDaddy()
    assert client._default_headers()["Authorization"] == "sso-key tk:ts"
    assert client.max_retries == 6


def test_explicit_settings_with_overrides():
    settings = load_settings(api_key="k", api_secret="s", timeout=3)
    client = GoDaddy(settings=settings, max_retries=0)
    assert client.timeout == 3
    assert client.max_retries == 0
    assert isinstance(client.settings, Settings)


def test_settings_reject_bad_values():
    with pytest.raises(ValueError):
        load_settings(api_key="k", api_secret="s", timeout=-1)


def test_secret_is_masked():
    settings = load_settings(api_key="key", api_secret="supersecret")
    assert "supersecret" not in repr(settings)
    assert "supersecret" not in repr(GoDaddy(settings=settings))


def test_user_agent_template():
    client = GoDaddy("k", "s", user_agent="my-app/{version}")
    assert client.user_agent.startswith("my-app/0.")


def test_headers_sent(gd, api):
    api.queue(200, [])
    gd.dns.list("example.com")
    headers = api.last.headers
    assert headers["authorization"] == "sso-key key:secret"
    assert headers["accept"] == "application/json"
    assert headers["user-agent"].startswith("godaddy-python-sdk/")


def test_endpoints_from_settings(api):
    import httpx

    http = httpx.Client(transport=httpx.MockTransport(api))
    client = GoDaddy("k", "s", http_client=http, api_version="v2")
    api.queue(200, [])
    client.dns.list("example.com", "A", "www")
    assert api.last.url.path == "/v2/domains/example.com/records/A/www"


def test_endpoint_override_from_env(monkeypatch, api):
    import httpx

    monkeypatch.setenv("GODADDY_ENDPOINTS__RECORDS", "/custom/{version}/zones/{domain}")
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = GoDaddy("k", "s", http_client=http)
    api.queue(200, [])
    client.dns.list("example.com")
    assert api.last.url.path == "/custom/v1/zones/example.com"


def test_endpoint_override_from_file(monkeypatch, tmp_path):
    (tmp_path / "godaddy.toml").write_text(
        'api_key = "k"\napi_secret = "s"\n\n[endpoints]\ntlds = "/{version}/catalog/tlds"\n'
    )
    settings = load_settings()
    assert settings.path("tlds") == "/v1/catalog/tlds"
    assert settings.path("domains") == "/v1/domains"


def test_path_values_are_quoted():
    settings = load_settings(api_key="k", api_secret="s")
    path = settings.path("record", domain="example.com", type="TXT", name="a b/c")
    assert path == "/v1/domains/example.com/records/TXT/a%20b%2Fc"
    assert settings.path("record", domain="example.com", type="A", name="@").endswith("/A/@")
