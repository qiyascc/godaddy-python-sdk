from __future__ import annotations

import httpx
import pytest

from godaddy import (
    APIConnectionError,
    AuthenticationError,
    DNSRecord,
    GoDaddy,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


def test_validation_error_fields(gd, api):
    api.queue(422, {
        "code": "INVALID_BODY",
        "message": "Request body doesn't fulfill schema",
        "fields": [{"path": "records[0].name", "code": "PATTERN", "message": "invalid name"}],
    })
    with pytest.raises(ValidationError) as info:
        gd.dns.add("example.com", DNSRecord.a("bad name", "1.1.1.1"))
    exc = info.value
    assert exc.status_code == 422
    assert exc.code == "INVALID_BODY"
    assert exc.fields[0].path == "records[0].name"
    assert "invalid name" in str(exc)


def test_status_mapping(gd, api):
    api.queue(401, {"code": "UNABLE_TO_AUTHENTICATE", "message": "bad key"})
    with pytest.raises(AuthenticationError):
        gd.dns.list("example.com")
    api.queue(404, {"code": "UNKNOWN_DOMAIN", "message": "nope"})
    with pytest.raises(NotFoundError):
        gd.domains.get("missing.com")


def test_non_json_error(gd, api):
    api.responses.append(httpx.Response(400, text="plain failure"))
    with pytest.raises(ValidationError, match="plain failure"):
        gd.dns.list("example.com")


def test_rate_limit_is_retried(gd, api):
    api.queue(429, {"code": "TOO_MANY_REQUESTS", "message": "slow down", "retryAfterSec": 1})
    api.queue(200, [])
    assert gd.dns.list("example.com") == []
    assert len(api.requests) == 2


def test_rate_limit_gives_up(gd, api):
    for _ in range(3):
        api.queue(429, {"code": "TOO_MANY_REQUESTS", "message": "slow down", "retryAfterSec": 7})
    with pytest.raises(RateLimitError) as info:
        gd.dns.list("example.com")
    assert info.value.retry_after == 7
    assert len(api.requests) == 3


def test_rate_limit_respects_max_wait(api):
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = GoDaddy("k", "s", http_client=http, max_retry_wait=5)
    api.queue(429, {"message": "slow down", "retryAfterSec": 600})
    with pytest.raises(RateLimitError):
        client.dns.list("example.com")
    assert len(api.requests) == 1


def test_server_error_retried_for_get_only(gd, api):
    api.queue(503, {"message": "busy"})
    api.queue(200, [])
    gd.dns.list("example.com")
    assert len(api.requests) == 2

    api.requests.clear()
    api.queue(503, {"message": "busy"})
    with pytest.raises(ServerError):
        gd.dns.add("example.com", DNSRecord.a("x", "1.1.1.1"))
    assert len(api.requests) == 1


def test_connection_error():
    def broken(request):
        raise httpx.ConnectError("refused", request=request)

    http = httpx.Client(transport=httpx.MockTransport(broken))
    client = GoDaddy("k", "s", http_client=http, max_retries=0)
    with pytest.raises(APIConnectionError):
        client.dns.list("example.com")
