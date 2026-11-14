# Moving between providers

This SDK is one of four with the same shape: GoDaddy, Namecheap, Hostinger and DigitalOcean. The common methods take the same arguments in the same order, so code that only uses them works with any of the four clients. This page shows how to use that, and walks through copying a zone from GoDaddy to DigitalOcean.

## What is the same

| Method | Same in all four |
| --- | --- |
| `dns.list(domain, type=None, name=None)` | Yes. Returns `list[DNSRecord]`. |
| `dns.exists(domain, type, name)` | Yes. Returns `bool`. |
| `dns.add(domain, *records)` | Yes. Records are each SDK's own `DNSRecord`. |
| `dns.replace(domain, type, name, values, ttl=...)` | Yes. |
| `dns.point(domain, name, ip, ttl=...)` | Yes. `A` or `AAAA` from the address. |
| `dns.unpoint(domain, name, ip_version=4)` | Yes. Does nothing if the record is gone. |
| `dns.alias(domain, name, target, ttl=...)` | Yes. Sets a `CNAME`. |
| `dns.set_txt(domain, name, values, ttl=...)` | Yes. |

Every `DNSRecord` has `type`, `name`, `data` and `ttl`, and names are relative to the domain with `@` for the apex.

## What differs

| | GoDaddy | Namecheap | Hostinger | DigitalOcean |
| --- | --- | --- | --- | --- |
| Credentials | key and secret, or token | API user, key and whitelisted IP | token | token |
| Delete | `delete(domain, type, name, missing_ok=)` | `delete(domain, type, name, data=)` | `delete(domain, type, name, data=)` | `delete(domain, record_id)` and `delete_all(domain, type, name)` |
| Default TTL | 600 | 1800 | 14400 | 1800 |
| `MX` priority | `priority` field | `priority` field | inside `data`, like `10 mx.example.com.` | `priority` field |
| Zone | the domain must be in the account | the domain must be in the account and use Namecheap DNS | the domain must be in the account | create it with `domains.create` |

## Code that works with any of them

Write against the shared methods and pass the client in:

```python
def launch_preview(client, branch: str, ip: str) -> str:
    name = f"{branch}.preview"
    client.dns.point("example.com", name, ip)
    return f"{name}.example.com"


def close_preview(client, branch: str) -> None:
    client.dns.unpoint("example.com", f"{branch}.preview")
```

```python
from godaddy import GoDaddy
from digitalocean_sdk import DigitalOcean

with GoDaddy() as gd:
    launch_preview(gd, "feature-login", "203.0.113.50")

with DigitalOcean() as do:
    launch_preview(do, "feature-login", "203.0.113.50")
```

## Copying a zone from GoDaddy to DigitalOcean

Install both SDKs and set both sets of credentials:

```bash
pip install godaddy-python-sdk digitalocean-python-sdk
export GODADDY_API_KEY=...
export GODADDY_API_SECRET=...
export DIGITALOCEAN_TOKEN=...
```

```python
from collections import defaultdict

from digitalocean_sdk import DigitalOcean
from digitalocean_sdk import DNSRecord as TargetRecord
from godaddy import GoDaddy

ZONE = "example.com"
SIMPLE = {"A", "AAAA", "CNAME", "TXT"}

with GoDaddy() as source, DigitalOcean() as target:
    records = source.dns.list(ZONE)

    if not target.domains.exists(ZONE):
        target.domains.create(ZONE)

    groups = defaultdict(list)
    for record in records:
        if record.type in SIMPLE or record.type == "MX":
            groups[(record.type, record.name)].append(record)

    for (kind, name), rows in sorted(groups.items()):
        ttl = max(row.ttl for row in rows)
        if kind == "MX":
            values = [TargetRecord.mx(name, row.data, priority=row.priority or 10, ttl=ttl) for row in rows]
        else:
            values = [row.data for row in rows]
        target.dns.replace(ZONE, kind, name, values, ttl=ttl)
        print(f"{kind:5} {name:20} {len(rows)} record(s)")
```

What the script does:

1. Reads the whole zone from GoDaddy.
2. Creates the zone at DigitalOcean if it is not there yet.
3. Groups records by type and name, because `replace` writes one set at a time.
4. Writes each set. `MX` records become DigitalOcean `DNSRecord`s so the priority goes along. The other types are plain values.

`NS` and `SOA` records are skipped on purpose: the new provider has its own. `SRV` and `CAA` are left out to keep the example short. Add them the same way as `MX`, with the target SDK's `DNSRecord.srv` and `DNSRecord.caa`.

The script can run more than once. `replace` makes each set match the source, so a second run only fixes what changed.

## Switching over

1. Copy the zone with the script above.
2. Compare: list the zone at both providers and check that every name you care about is there.
3. Lower the TTLs at the old provider a day ahead, so caches turn over quickly.
4. Change the name servers at the registrar to the new provider. For DigitalOcean those are `ns1.digitalocean.com`, `ns2.digitalocean.com` and `ns3.digitalocean.com`. With GoDaddy as registrar this is `source.domains.update(ZONE, name_servers=[...])`.
5. Keep the old zone for a few days, until the change has spread.

## The other directions

The same plan works between any two of the four. Swap the imports and adjust for the differences in the table above, mainly how `MX` priority is stored and whether the zone has to be created first.

- [GoDaddy SDK docs](https://godaddy-python-sdk.readthedocs.io/en/latest/)
- [Namecheap SDK docs](https://namecheap-python-sdk.readthedocs.io/en/latest/)
- [Hostinger SDK docs](https://hostinger-python-sdk.readthedocs.io/en/latest/)
- [DigitalOcean SDK docs](https://digitalocean-python-sdk.readthedocs.io/en/latest/)
