# Quickstart

This page builds one small script step by step: it lists the domains in your account, shows the DNS records of one of them, and points a subdomain at a server. It assumes you have [installed the package](installation.md) and have a [key pair](credentials.md).

## 1. Give the SDK your key

Set the key and secret as environment variables in the terminal you will run the script from.

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
export GODADDY_API_KEY=your-key
export GODADDY_API_SECRET=your-secret
```
:::

:::{tab-item} Windows (CMD)
```bat
set GODADDY_API_KEY=your-key
set GODADDY_API_SECRET=your-secret
```
:::
::::

With the variables set, `GoDaddy()` needs no arguments. You could also pass them in code, `GoDaddy("your-key", "your-secret")`, but then they end up in your source file.

To practise without touching real DNS, use OTE keys and also set `GODADDY_ENVIRONMENT=ote`.

## 2. List your domains

Create `first.py`:

```python
from godaddy import GoDaddy

with GoDaddy() as gd:
    for domain in gd.domains.iter():
        print(domain.domain, domain.status, domain.expires)
```

Run it:

```bash
python first.py
```

```text
example.com ACTIVE 2027-03-14 09:21:07+00:00
example.net ACTIVE 2026-12-02 18:40:51+00:00
```

What happens here:

- `GoDaddy()` reads the settings, builds the `Authorization` header and opens an HTTP connection pool. It does not send a request yet.
- `with` closes the connection pool when the block ends.
- `gd.domains.iter()` asks GoDaddy for one page of domains at a time and yields them one by one. Each item is a {py:class}`~godaddy.Domain` dataclass.

## 3. Read the DNS records

Add this inside the `with` block:

```python
    for record in gd.dns.list("example.com"):
        print(record.type, record.name, record.data, record.ttl)
```

```text
A @ 203.0.113.1 600
CNAME www @ 3600
MX @ mail.example.com 3600
NS @ ns11.domaincontrol.com 3600
```

Names are relative to the domain, so `@` is `example.com` itself and `www` is `www.example.com`. Each row is a {py:class}`~godaddy.DNSRecord`.

To narrow the list, pass a type, or a type and a name:

```python
gd.dns.list("example.com", "A")
gd.dns.list("example.com", "A", "www")
```

## 4. Point a subdomain at a server

```python
    gd.dns.point("example.com", "shop", "203.0.113.10")
    print(gd.dns.list("example.com", "A", "shop"))
```

```text
[DNSRecord(type='A', name='shop', data='203.0.113.10', ttl=600, priority=None, weight=None, port=None, service=None, protocol=None)]
```

`point` looks at the address: an IPv4 address becomes an `A` record, an IPv6 address an `AAAA` record. Any records `shop` already had of that type are replaced. Run the script twice and nothing changes the second time, so it is safe to repeat.

DNS changes take a little while to reach resolvers around the world. Check from your machine with:

```bash
nslookup shop.example.com
```

## 5. Handle errors

Wrap the calls so a typo in the domain or a revoked key gives a clear message:

```python
from godaddy import GoDaddy, GoDaddyError, NotFoundError

try:
    with GoDaddy() as gd:
        gd.dns.point("example.com", "shop", "203.0.113.10")
except NotFoundError:
    print("example.com is not in this GoDaddy account")
except GoDaddyError as exc:
    print("GoDaddy said:", exc)
```

Every exception the SDK raises inherits from {py:class}`~godaddy.GoDaddyError`. [](errors.md) lists them all.

## The same script, async

```python
import asyncio

from godaddy import AsyncGoDaddy


async def main() -> None:
    async with AsyncGoDaddy() as gd:
        async for domain in gd.domains.iter():
            print(domain.domain)
        await gd.dns.point("example.com", "shop", "203.0.113.10")


asyncio.run(main())
```

## Where to go next

- [](configuration.md): all settings and the three ways to set them.
- [](dns.md): every DNS method in detail.
- [](domains.md): availability checks, suggestions and domain settings.
- [](examples/index.md): complete scripts for common jobs.
