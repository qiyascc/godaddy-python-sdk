# Domains

`gd.domains` covers the domains in your account and the questions you ask before buying one: is it free, what does it cost, what else is there.

## Listing your domains

### `iter`

```python
for domain in gd.domains.iter():
    print(domain.domain, domain.expires, domain.renew_auto)
```

`iter()` walks through the whole portfolio and yields one {py:class}`~godaddy.Domain` at a time. Behind the scenes it asks for pages of `page_size` domains (default 100) and uses the last domain of each page as the marker for the next one. It stops when a page comes back short. Use it when you want everything and do not care about pages.

It accepts the same filters as `list`, without `limit` and `marker`:

```python
for domain in gd.domains.iter(statuses=["ACTIVE"]):
    ...
```

### `list`

```python
page = gd.domains.list(limit=50)
next_page = gd.domains.list(limit=50, marker=page[-1].domain)
```

`list()` returns a single page as a `list[Domain]`. All arguments are keyword only and passed through to GoDaddy:

| Argument | Sent as | Meaning |
| --- | --- | --- |
| `statuses` | `statuses` | Only domains in these statuses, for example `["ACTIVE"]`. |
| `status_groups` | `statusGroups` | Only domains in these status groups. |
| `limit` | `limit` | Page size. |
| `marker` | `marker` | Start after this domain name. |
| `includes` | `includes` | Extra data GoDaddy should include in each item. |

List values are joined with commas. The accepted status names and include values are defined by GoDaddy's API.

### The Domain dataclass

| Field | Type | Meaning |
| --- | --- | --- |
| `domain` | `str` | The name, for example `example.com`. |
| `domain_id` | `int` or `None` | GoDaddy's id. |
| `status` | `str` | For example `ACTIVE`. |
| `created_at` | `datetime` or `None` | When it was registered. |
| `expires` | `datetime` or `None` | When it expires. |
| `renew_auto` | `bool` | Auto renewal is on. |
| `renewable` | `bool` | It can be renewed now. |
| `locked` | `bool` | Transfer lock is on. |
| `privacy` | `bool` | Privacy protection is on. |
| `expiration_protected` | `bool` | |
| `transfer_protected` | `bool` | |
| `name_servers` | `list[str]` | Name servers, when GoDaddy includes them. |
| `registrant` | `Contact` or `None` | Registrant contact, when included. |
| `raw` | `dict` | The full JSON object GoDaddy sent, for fields the dataclass does not map. |

Dates are parsed from the ISO timestamps GoDaddy sends, so they carry the time zone GoDaddy gives them.

## One domain

```python
info = gd.domains.get("example.com")
print(info.status, info.expires, info.name_servers)
print(info.registrant.email if info.registrant else "no registrant data")
```

Returns a `Domain`. A domain that is not in your account raises `NotFoundError`.

The registrant is a {py:class}`~godaddy.Contact` with `first_name`, `last_name`, `email`, `phone`, `organization` and the original `raw` dict.

## Checking availability

### One name

```python
check = gd.domains.available("my-new-idea.com")
if check.available:
    print(f"{check.domain} is free: {check.price} {check.currency} for {check.period} year(s)")
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `domain` | | The full name, including the TLD. |
| `full_check` | `False` | `True` asks GoDaddy for a full check (`checkType=FULL`) instead of the fast cached one (`FAST`). |
| `for_transfer` | `False` | Check whether the name can be transferred in, not registered. |

The result is an {py:class}`~godaddy.Availability`:

| Field | Meaning |
| --- | --- |
| `domain` | The name that was checked. |
| `available` | `True` if it can be registered. |
| `definitive` | `True` if GoDaddy is sure. Fast checks may come back as not definitive. |
| `price` | A `Decimal` in normal currency units, or `None`. |
| `currency` | For example `USD`. |
| `period` | Registration period in years. |
| `raw` | The original JSON. |

GoDaddy sends prices in micro units (millionths). The SDK divides by 1,000,000 for you, so `price` is ready to show, for example `Decimal('11.99')`.

### Many names

```python
results = gd.domains.available_many(["one.com", "two.net", "three.org"])
for row in results:
    print(row.domain, row.available, row.price)
```

Sends one request for the whole list and returns a `list[Availability]`. `full_check=True` works here too. An empty list raises `ValueError`.

## Suggestions

```python
for suggestion in gd.domains.suggest("coffee shop baku", limit=10, tlds=["com", "az"]):
    print(suggestion.domain)
```

| Argument | Sent as | Meaning |
| --- | --- | --- |
| `query` | `query` | Words or a domain to build ideas from. |
| `limit` | `limit` | How many suggestions. |
| `tlds` | `tlds` | Only these TLDs. |
| `country` | `country` | Country hint. |
| `city` | `city` | City hint. |
| `length_min` | `lengthMin` | Shortest name. |
| `length_max` | `lengthMax` | Longest name. |
| `wait_ms` | `waitMs` | How long GoDaddy may spend building the list. |

Each item is a {py:class}`~godaddy.Suggestion` with a single `domain` field. Suggestions are ideas, not availability checks, so run them through `available_many` before you show prices.

## TLDs

```python
for tld in gd.domains.tlds():
    print(tld.name, tld.type)
```

Returns the TLDs GoDaddy sells, as {py:class}`~godaddy.Tld` objects with `name` and `type`.

## Changing domain settings

```python
gd.domains.update("example.com", renew_auto=True, locked=True)
gd.domains.update("example.com", name_servers=["ns1.example.net", "ns2.example.net"])
```

| Argument | Sent as | Meaning |
| --- | --- | --- |
| `locked` | `locked` | Turn the transfer lock on or off. |
| `renew_auto` | `renewAuto` | Turn auto renewal on or off. |
| `name_servers` | `nameServers` | Replace the name servers. |
| `subaccount_id` | `subaccountId` | Move the domain to a sub account (resellers). |

Only the arguments you pass are sent. Calling `update` with nothing to change raises `ValueError`. Returns `None`.

```{warning}
Changing `name_servers` moves the domain's DNS away from GoDaddy (or back). After that, records you edit with `gd.dns` no longer affect the live domain until the name servers point at GoDaddy again.
```

## A worked example: renewal report

Print every domain that expires in the next 60 days and does not renew on its own:

```python
from datetime import date, timedelta

from godaddy import GoDaddy

soon = date.today() + timedelta(days=60)

with GoDaddy() as gd:
    for domain in gd.domains.iter(statuses=["ACTIVE"]):
        if domain.expires and domain.expires.date() < soon and not domain.renew_auto:
            days = (domain.expires.date() - date.today()).days
            print(f"{domain.domain} expires in {days} days and will not renew")
```

Schedule it once a week with the help of [](examples/scheduled-jobs.md).
