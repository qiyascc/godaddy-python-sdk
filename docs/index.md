# GoDaddy Python SDK

A small, typed Python client for the GoDaddy Domains and DNS API. It works in sync and async code, waits and retries when GoDaddy rate limits you, and gives you plain dataclasses instead of raw JSON.

```python
from godaddy import GoDaddy

with GoDaddy("API_KEY", "API_SECRET") as gd:
    gd.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`. If `shop` already had `A` records, they are replaced.

The package is on PyPI as `godaddy-python-sdk` and is imported as `godaddy`. It needs Python 3.10 or newer.

## Where to start

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: installation
:link-type: doc

Set up a virtual environment, install the package with pip, uv or Poetry, and check that it imports.
:::

:::{grid-item-card} API keys
:link: credentials
:link-type: doc

Create a key pair or a personal access token on the GoDaddy developer portal and pick the right environment.
:::

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc

Write your first script: list the domains in your account and point a subdomain at a server.
:::

:::{grid-item-card} Configuration
:link: configuration
:link-type: doc

Pass settings in code, through `GODADDY_*` environment variables or from a TOML, YAML or JSON file.
:::

:::{grid-item-card} DNS records
:link: dns
:link-type: doc

List, add, replace and delete records, plus the `point`, `alias` and `set_txt` shortcuts.
:::

:::{grid-item-card} Domains
:link: domains
:link-type: doc

Walk through your portfolio, check availability and prices, get suggestions and change domain settings.
:::

:::{grid-item-card} Recipes
:link: examples/index
:link-type: doc

Complete scripts: a subdomain per customer, dynamic DNS, Let's Encrypt DNS-01, Django and FastAPI.
:::

:::{grid-item-card} API reference
:link: api
:link-type: doc

Every public class, method and exception with its signature.
:::
::::

## What the SDK covers

- DNS: list, get, check, add, replace, rewrite a type, rewrite the whole zone and delete records.
- DNS shortcuts: `point`, `unpoint`, `alias` and `set_txt` for the jobs people do every day.
- Domains: list and iterate over your portfolio, read one domain, check availability one by one or in bulk, get name suggestions, list TLDs and update locking, auto renewal and name servers.
- Typed errors for every status code GoDaddy returns, with the failing fields attached.
- Automatic retries for rate limits, server errors and dropped connections, only where a retry is safe.
- Settings through [goodconf](https://github.com/lincolnloop/goodconf): code, environment variables or a config file.
- Every message the SDK prints lives in a YAML file you can translate.

It has three siblings with the same shape: the [Namecheap](https://namecheap-python-sdk.readthedocs.io/en/latest/), [Hostinger](https://hostinger-python-sdk.readthedocs.io/en/latest/) and [DigitalOcean](https://digitalocean-python-sdk.readthedocs.io/en/latest/) SDKs. `dns.point("example.com", "shop", ip)` does the same thing in all four, so moving a zone between providers does not mean learning a new library.

```{toctree}
:hidden:
:caption: Getting started

installation
credentials
quickstart
configuration
```

```{toctree}
:hidden:
:caption: Guides

dns
domains
async
errors
retries-timeouts
http-client
messages
testing
```

```{toctree}
:hidden:
:caption: Examples

examples/index
examples/customer-subdomains
examples/dynamic-dns
examples/acme-dns-01
examples/migrate-between-providers
examples/web-frameworks
examples/scheduled-jobs
```

```{toctree}
:hidden:
:caption: Reference

api
settings
faq
changelog
```

```{toctree}
:hidden:
:caption: Project

development
about
```
