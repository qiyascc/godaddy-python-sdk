# DNS records

Everything under `gd.dns` works on the DNS zone of a domain in your GoDaddy account. The records only take effect on the internet while the domain uses GoDaddy's name servers.

## Names, types and the apex

Every method takes the domain first. Record names are **relative to the domain**:

| You want | Pass as `name` |
| --- | --- |
| `example.com` itself (the apex) | `@` |
| `www.example.com` | `www` |
| `api.eu.example.com` | `api.eu` |
| `_acme-challenge.example.com` | `_acme-challenge` |

The domain is cleaned before use: `" Example.COM. "` becomes `example.com`. An empty domain raises `ValueError`, and so does an empty name in the methods that need one, with a hint to use `@` for the apex.

The record type can be a plain string (`"A"`, `"cname"`) or a member of {py:class}`~godaddy.RecordType`: `A`, `AAAA`, `CNAME`, `MX`, `NS`, `SOA`, `SRV`, `TXT` and `CAA`. Strings are upper cased for you.

## The DNSRecord dataclass

Reads return {py:class}`~godaddy.DNSRecord` objects and writes accept them.

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=600, priority=None, weight=None, port=None, service=None, protocol=None)
```

| Field | Meaning |
| --- | --- |
| `type` | Record type, always upper case. |
| `name` | Name relative to the domain, `@` for the apex. |
| `data` | The value: an address for `A`/`AAAA`, a host for `CNAME`/`MX`/`NS`/`SRV`, text for `TXT`. |
| `ttl` | Time to live in seconds. Defaults to 600. |
| `priority` | `MX` and `SRV` only. |
| `weight`, `port`, `service`, `protocol` | `SRV` only. |

Build records with the class methods instead of filling the fields by hand. They validate addresses and set sensible defaults:

```python
from godaddy import DNSRecord

DNSRecord.a("www", "203.0.113.10")
DNSRecord.aaaa("www", "2001:db8::10")
DNSRecord.cname("blog", "example.github.io")
DNSRecord.txt("@", "v=spf1 include:_spf.example.net ~all")
DNSRecord.mx("@", "mail.example.com", priority=10)
DNSRecord.srv("_sip", "_tcp", "@", "sip.example.com", port=5060, priority=10, weight=5)
```

| Constructor | Default TTL | Notes |
| --- | --- | --- |
| `a(name, ip, ttl=600)` | 600 | Raises `ValueError` if `ip` is not an IPv4 address. |
| `aaaa(name, ip, ttl=600)` | 600 | Raises `ValueError` if `ip` is not an IPv6 address. |
| `cname(name, target, ttl=3600)` | 3600 | |
| `txt(name, value, ttl=600)` | 600 | |
| `mx(name, host, priority=10, ttl=3600)` | 3600 | |
| `srv(service, protocol, name, target, port, priority=0, weight=0, ttl=3600)` | 3600 | `service` like `_sip`, `protocol` like `_tcp`. |

## Reading records

### `list`

```python
gd.dns.list("example.com")
gd.dns.list("example.com", "A")
gd.dns.list("example.com", "A", "www")
gd.dns.list("example.com", name="www")
```

Returns a `list[DNSRecord]`, empty when nothing matches.

| Arguments | What is fetched |
| --- | --- |
| domain only | The whole zone. |
| domain and `type` | All records of that type, filtered by GoDaddy. |
| domain, `type` and `name` | Records of that type and name, filtered by GoDaddy. |
| domain and `name` only | The whole zone, then filtered to that name in Python. |

`offset` and `limit` are passed to GoDaddy for paging through large zones:

```python
first_page = gd.dns.list("example.com", offset=0, limit=100)
```

### `get`

```python
gd.dns.get("example.com", "CNAME", "blog")
```

Same as `list` with a type and a name. It returns a list, because one name can hold several records of the same type (two `A` records for round robin, several `TXT` values).

### `exists`

```python
if gd.dns.exists("example.com", "A", "shop"):
    ...
```

Returns `True` when at least one record of that type and name exists.

If the domain itself is not in your account, these calls raise `NotFoundError` rather than returning an empty list.

## Changing records

GoDaddy offers four ways to write, from the most careful to the most sweeping.

| Method | HTTP | Effect |
| --- | --- | --- |
| `add` | `PATCH` | Appends records. Nothing is removed. |
| `replace` | `PUT` | Replaces every record of one type and one name. |
| `replace_type` | `PUT` | Replaces every record of one type, across all names. |
| `replace_all` | `PUT` | Replaces the whole zone. |

### `add`

```python
gd.dns.add(
    "example.com",
    DNSRecord.a("api", "203.0.113.20"),
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mail.example.com", priority=10),
)
```

Takes one or more `DNSRecord` objects after the domain and sends them in one request. Calling it with no records raises `ValueError`. Returns `None`.

```{note}
`add` is sent as a `PATCH`, which the SDK never retries after a server error, because a retry could add the same record twice. See [](retries-timeouts.md).
```

### `replace`

```python
gd.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)
gd.dns.replace("example.com", "TXT", "@", "v=spf1 -all")
gd.dns.replace("example.com", "MX", "@", [
    DNSRecord.mx("@", "mx1.example.net", priority=10),
    DNSRecord.mx("@", "mx2.example.net", priority=20),
])
```

After the call, the type and name hold exactly the values you passed, nothing else. `values` can be:

- one string,
- a list of strings, which all get the `ttl` argument (default 600),
- one `DNSRecord` or a list of them, which keep their own TTL and extra fields such as `priority`.

Use `DNSRecord` values for `MX` and `SRV`, since a plain string has nowhere to put the priority. An empty list raises `ValueError`.

### `replace_type`

```python
gd.dns.replace_type("example.com", "A", [
    DNSRecord.a("@", "203.0.113.10"),
    DNSRecord.a("www", "203.0.113.10"),
    DNSRecord.a("api", "203.0.113.20"),
])
```

Replaces every record of that type in the zone. `A` records you leave out of the list are deleted. Every record in the list must have the type you named, or the call raises `ValueError` before anything is sent.

### `replace_all`

```python
gd.dns.replace_all("example.com", [
    DNSRecord.a("@", "203.0.113.10"),
    DNSRecord.cname("www", "@"),
    DNSRecord.mx("@", "mail.example.com"),
])
```

```{danger}
`replace_all` rewrites the whole zone. Every record you leave out is removed, including `MX` records for your mail and `TXT` records for domain verification. Read the zone first with `gd.dns.list(domain)`, change the list in Python, then write it back.
```

### `delete`

```python
gd.dns.delete("example.com", "A", "old")
gd.dns.delete("example.com", "A", "maybe-gone", missing_ok=True)
```

Deletes every record of that type and name. If there is nothing to delete, GoDaddy answers 404 and the SDK raises `NotFoundError`, unless you pass `missing_ok=True`, in which case the call just returns `None`.

## Shortcuts

Four methods cover the jobs people do most. They are thin wrappers around `replace` and `delete`.

### `point`

```python
gd.dns.point("example.com", "shop", "203.0.113.10")
gd.dns.point("example.com", "shop", "2001:db8::10", ttl=300)
```

Makes `shop.example.com` resolve to the address. IPv4 gives an `A` record, IPv6 an `AAAA` record. Existing records of that type and name are replaced. An invalid address raises `ValueError` before any request.

### `unpoint`

```python
gd.dns.unpoint("example.com", "shop")
gd.dns.unpoint("example.com", "shop", ip_version=6)
```

Deletes the `A` records (or `AAAA` with `ip_version=6`) of that name. It does nothing if they are already gone.

### `alias`

```python
gd.dns.alias("example.com", "docs", "example.github.io")
```

Sets a `CNAME` with a default TTL of 3600 seconds. A name that has a `CNAME` cannot have any other record, so remove other records of that name first if GoDaddy refuses.

### `set_txt`

```python
gd.dns.set_txt("example.com", "@", "v=spf1 include:_spf.example.net ~all")
gd.dns.set_txt("example.com", "_acme-challenge", ["token-one", "token-two"], ttl=600)
```

Replaces the `TXT` values of that name with one value or a list.

## A worked example: moving a site to a new server

The site runs on `203.0.113.10` and moves to `198.51.100.7`. Every `A` record pointing at the old address should follow, and nothing else should change.

```python
from godaddy import GoDaddy

OLD, NEW = "203.0.113.10", "198.51.100.7"

with GoDaddy() as gd:
    names = sorted({r.name for r in gd.dns.list("example.com", "A") if r.data == OLD})
    for name in names:
        gd.dns.point("example.com", name, NEW, ttl=600)
        print(f"{name}: {OLD} -> {NEW}")
```

Lower the TTL a day before the move (for example `ttl=300`) and caches will pick up the new address faster on the day.

## Async

`AsyncGoDaddy().dns` has the same methods with the same arguments. Await them:

```python
async with AsyncGoDaddy() as gd:
    records = await gd.dns.list("example.com", "A")
    await gd.dns.point("example.com", "shop", "203.0.113.10")
```

See [](async.md) for more.
