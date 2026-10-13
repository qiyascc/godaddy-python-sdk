from __future__ import annotations

from decimal import Decimal

import pytest

from godaddy import Domain


def test_get(gd, api):
    api.queue(200, {
        "domain": "example.com",
        "domainId": 42,
        "status": "ACTIVE",
        "expires": "2027-01-02T03:04:05.000Z",
        "renewAuto": True,
        "locked": True,
        "nameServers": ["ns1.example.net", "ns2.example.net"],
        "contactRegistrant": {"nameFirst": "Ada", "nameLast": "Lovelace", "email": "ada@example.com"},
    })
    domain = gd.domains.get("example.com")
    assert isinstance(domain, Domain)
    assert domain.domain_id == 42
    assert domain.expires.year == 2027
    assert domain.renew_auto and domain.locked
    assert domain.registrant.first_name == "Ada"


def test_list_params(gd, api):
    api.queue(200, [{"domain": "a.com"}])
    gd.domains.list(statuses=["ACTIVE", "PENDING"], limit=10)
    params = api.last.url.params
    assert params["statuses"] == "ACTIVE,PENDING"
    assert params["limit"] == "10"
    assert "marker" not in params


def test_iter_pages_with_marker(gd, api):
    gd.domains.page_size = 2
    api.queue(200, [{"domain": "a.com"}, {"domain": "b.com"}])
    api.queue(200, [{"domain": "c.com"}])
    names = [d.domain for d in gd.domains.iter()]
    assert names == ["a.com", "b.com", "c.com"]
    assert api.requests[1].url.params["marker"] == "b.com"


def test_available(gd, api):
    api.queue(200, {"domain": "idea.com", "available": True, "price": 11990000, "currency": "USD", "period": 1})
    result = gd.domains.available("Idea.com", full_check=True)
    assert result.available is True
    assert result.price == Decimal("11.99")
    assert api.last.url.params["checkType"] == "FULL"
    assert api.last.url.params["forTransfer"] == "false"
    assert api.last.url.params["domain"] == "idea.com"


def test_available_many(gd, api):
    api.queue(200, {"domains": [{"domain": "a.com", "available": False}, {"domain": "b.net", "available": True}]})
    results = gd.domains.available_many(["a.com", "b.net"])
    assert api.last.method == "POST"
    assert api.body() == ["a.com", "b.net"]
    assert [r.available for r in results] == [False, True]


def test_suggest_and_tlds(gd, api):
    api.queue(200, [{"domain": "coffeebaku.com"}])
    api.queue(200, [{"name": "com", "type": "GENERIC"}])
    assert gd.domains.suggest("coffee baku", limit=3, tlds=["com", "az"])[0].domain == "coffeebaku.com"
    assert api.requests[0].url.params["tlds"] == "com,az"
    assert gd.domains.tlds()[0].type == "GENERIC"


def test_update(gd, api):
    api.queue(204)
    gd.domains.update("example.com", renew_auto=False, name_servers=["ns1.x.net"])
    assert api.last.method == "PATCH"
    assert api.body() == {"renewAuto": False, "nameServers": ["ns1.x.net"]}
    with pytest.raises(ValueError):
        gd.domains.update("example.com")
