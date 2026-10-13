from __future__ import annotations

import pytest

from godaddy import DNSRecord, NotFoundError


async def test_async_dns(agd, api):
    api.queue(200, [{"type": "A", "name": "www", "data": "1.2.3.4", "ttl": 600}])
    records = await agd.dns.list("example.com", "A")
    assert records == [DNSRecord("A", "www", "1.2.3.4", 600)]


async def test_async_point_and_exists(agd, api):
    api.queue(200)
    api.queue(200, [{"type": "A", "name": "shop", "data": "203.0.113.10"}])
    await agd.dns.point("example.com", "shop", "203.0.113.10")
    assert await agd.dns.exists("example.com", "A", "shop") is True


async def test_async_iter(agd, api):
    agd.domains.page_size = 1
    api.queue(200, [{"domain": "a.com"}])
    api.queue(200, [])
    names = [d.domain async for d in agd.domains.iter()]
    assert names == ["a.com"]


async def test_async_retry_and_errors(agd, api):
    api.queue(500, {"message": "oops"})
    api.queue(200, [])
    assert await agd.dns.list("example.com") == []
    api.queue(404, {"message": "missing"})
    with pytest.raises(NotFoundError):
        await agd.domains.get("missing.com")


async def test_async_context_manager(api):
    import httpx

    from godaddy import AsyncGoDaddy

    async with AsyncGoDaddy("k", "s", http_client=httpx.AsyncClient(transport=httpx.MockTransport(api))) as client:
        api.queue(200, [])
        assert await client.dns.list("example.com") == []
