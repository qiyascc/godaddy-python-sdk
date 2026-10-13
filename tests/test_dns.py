from __future__ import annotations

import pytest

from godaddy import DNSRecord, RecordType


def test_list_all(gd, api):
    api.queue(200, [
        {"type": "A", "name": "@", "data": "1.2.3.4", "ttl": 600},
        {"type": "MX", "name": "@", "data": "mail.example.com", "ttl": 3600, "priority": 10},
    ])
    records = gd.dns.list("Example.com")
    assert api.last.method == "GET"
    assert api.last.url.path == "/v1/domains/example.com/records"
    assert records[0] == DNSRecord("A", "@", "1.2.3.4", 600)
    assert records[1].priority == 10


def test_list_by_type_and_name(gd, api):
    api.queue(200, [{"type": "A", "name": "www", "data": "1.2.3.4", "ttl": 600}])
    gd.dns.list("example.com", RecordType.A, "www", limit=5)
    assert api.last.url.path == "/v1/domains/example.com/records/A/www"
    assert api.last.url.params["limit"] == "5"


def test_list_by_name_only_filters_locally(gd, api):
    api.queue(200, [
        {"type": "A", "name": "www", "data": "1.2.3.4"},
        {"type": "A", "name": "api", "data": "1.2.3.5"},
        {"type": "CNAME", "name": "www", "data": "x.example.net"},
    ])
    records = gd.dns.list("example.com", name="www")
    assert api.last.url.path == "/v1/domains/example.com/records"
    assert [r.type for r in records] == ["A", "CNAME"]


def test_exists(gd, api):
    api.queue(200, [{"type": "A", "name": "shop", "data": "1.2.3.4"}])
    api.queue(200, [])
    assert gd.dns.exists("example.com", "a", "shop") is True
    assert gd.dns.exists("example.com", "A", "nope") is False


def test_add(gd, api):
    api.queue(200)
    gd.dns.add("example.com", DNSRecord.a("api", "10.0.0.1"), DNSRecord.mx("@", "mx.example.com", priority=5))
    assert api.last.method == "PATCH"
    assert api.body() == [
        {"type": "A", "name": "api", "data": "10.0.0.1", "ttl": 600},
        {"type": "MX", "name": "@", "data": "mx.example.com", "ttl": 3600, "priority": 5},
    ]


def test_add_needs_records(gd):
    with pytest.raises(ValueError):
        gd.dns.add("example.com")


def test_replace_with_values(gd, api):
    api.queue(200)
    gd.dns.replace("example.com", "A", "www", ["1.1.1.1", "2.2.2.2"], ttl=1200)
    assert api.last.method == "PUT"
    assert api.last.url.path == "/v1/domains/example.com/records/A/www"
    assert api.body() == [{"data": "1.1.1.1", "ttl": 1200}, {"data": "2.2.2.2", "ttl": 1200}]


def test_replace_type_checks_records(gd, api):
    with pytest.raises(ValueError):
        gd.dns.replace_type("example.com", "A", [DNSRecord.txt("@", "x")])
    api.queue(200)
    gd.dns.replace_type("example.com", "A", [DNSRecord.a("www", "1.1.1.1")])
    assert api.body() == [{"name": "www", "data": "1.1.1.1", "ttl": 600}]


def test_replace_all(gd, api):
    api.queue(200)
    gd.dns.replace_all("example.com", [DNSRecord.a("@", "1.1.1.1")])
    assert api.last.url.path == "/v1/domains/example.com/records"
    assert api.body() == [{"type": "A", "name": "@", "data": "1.1.1.1", "ttl": 600}]


def test_delete(gd, api):
    api.queue(204)
    assert gd.dns.delete("example.com", "A", "old") is None
    assert api.last.method == "DELETE"
    assert api.last.url.path == "/v1/domains/example.com/records/A/old"


def test_delete_missing_ok(gd, api):
    api.queue(404, {"code": "NOT_FOUND", "message": "Not found"})
    assert gd.dns.delete("example.com", "A", "gone", missing_ok=True) is None


def test_point_picks_record_type(gd, api):
    api.queue(200)
    api.queue(200)
    gd.dns.point("example.com", "shop", "203.0.113.10")
    assert api.requests[0].url.path == "/v1/domains/example.com/records/A/shop"
    gd.dns.point("example.com", "shop", "2001:db8::1", ttl=900)
    assert api.requests[1].url.path == "/v1/domains/example.com/records/AAAA/shop"
    assert api.body() == [{"data": "2001:db8::1", "ttl": 900}]


def test_point_rejects_bad_ip(gd):
    with pytest.raises(ValueError):
        gd.dns.point("example.com", "shop", "not-an-ip")


def test_alias_and_txt(gd, api):
    api.queue(200)
    api.queue(200)
    gd.dns.alias("example.com", "docs", "example.github.io")
    assert api.requests[0].url.path == "/v1/domains/example.com/records/CNAME/docs"
    gd.dns.set_txt("example.com", "_acme-challenge", "token")
    assert api.requests[1].url.path == "/v1/domains/example.com/records/TXT/_acme-challenge"
    assert api.body() == [{"data": "token", "ttl": 600}]


def test_unpoint_ignores_missing(gd, api):
    api.queue(404, {"code": "NOT_FOUND", "message": "nope"})
    gd.dns.unpoint("example.com", "shop")
    assert api.last.url.path == "/v1/domains/example.com/records/A/shop"


def test_empty_name_rejected(gd):
    with pytest.raises(ValueError):
        gd.dns.get("example.com", "A", " ")


def test_record_helpers():
    assert DNSRecord.a("www", "1.2.3.4").type == "A"
    assert DNSRecord.aaaa("www", "::1").data == "::1"
    srv = DNSRecord.srv("_sip", "_tcp", "@", "sip.example.com", 5060, priority=1, weight=2)
    assert srv.to_api()["port"] == 5060
    assert srv.to_api()["service"] == "_sip"
    assert DNSRecord("cname", "x", "y").type == "CNAME"
    with pytest.raises(ValueError):
        DNSRecord.a("www", "999.1.1.1")


def test_empty_type_rejected():
    with pytest.raises(ValueError, match="record type"):
        DNSRecord(" ", "www", "1.1.1.1")
