# godaddy-python-sdk

A small, typed Python client for the GoDaddy Domains and DNS API. It works with both sync and async code, retries when GoDaddy rate limits you, and returns plain dataclasses, not raw JSON.

```python
from godaddy import GoDaddy

with GoDaddy("API_KEY", "API_SECRET") as gd:
    gd.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`.

## Install

```bash
pip install git+https://github.com/qiyascc/godaddy-python-sdk.git
```

Requires Python 3.10 or newer. Dependencies: [httpx](https://www.python-httpx.org/), [goodconf](https://github.com/lincolnloop/goodconf), pydantic and PyYAML.

## Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf), so you can configure the client from code, from environment variables or from a config file. Values passed in code win over the environment, and the environment wins over the file.

Create a key pair at [developer.godaddy.com/keys](https://developer.godaddy.com/keys), then pick whichever option suits you:

```python
gd = GoDaddy("API_KEY", "API_SECRET")
```

```bash
export GODADDY_API_KEY=...
export GODADDY_API_SECRET=...
```

```toml
api_key = "..."
api_secret = "..."
environment = "production"
timeout = 15
```

With no arguments, the client looks for `godaddy.toml`, `godaddy.yaml`, `godaddy.yml` or `godaddy.json` in the working directory. To load a file from somewhere else, set `GODADDY_CONFIG=/path/to/file`, or pass `config_file=` to the client. YAML files need the `yaml` extra, and TOML files on Python 3.10 need the `toml` extra:

```bash
pip install "godaddy-python-sdk[yaml] @ git+https://github.com/qiyascc/godaddy-python-sdk.git"
```

| Setting | Env variable | Default |
| --- | --- | --- |
| `api_key` | `GODADDY_API_KEY` | |
| `api_secret` | `GODADDY_API_SECRET` | |
| `environment` | `GODADDY_ENVIRONMENT` | `production` |
| `base_url` | `GODADDY_BASE_URL` | taken from `environment` |
| `production_url` | `GODADDY_PRODUCTION_URL` | `https://api.godaddy.com` |
| `ote_url` | `GODADDY_OTE_URL` | `https://api.ote-godaddy.com` |
| `api_version` | `GODADDY_API_VERSION` | `v1` |
| `endpoints.*` | `GODADDY_ENDPOINTS__<NAME>` | see below |
| `shopper_id` | `GODADDY_SHOPPER_ID` | |
| `timeout` | `GODADDY_TIMEOUT` | `30` |
| `max_retries` | `GODADDY_MAX_RETRIES` | `3` |
| `max_retry_wait` | `GODADDY_MAX_RETRY_WAIT` | `60` |
| `backoff_base` | `GODADDY_BACKOFF_BASE` | `0.5` |
| `backoff_cap` | `GODADDY_BACKOFF_CAP` | `8` |
| `page_size` | `GODADDY_PAGE_SIZE` | `100` |
| `user_agent` | `GODADDY_USER_AGENT` | `godaddy-python-sdk/{version}` |

Any setting can also be passed straight to the client, for example `GoDaddy(timeout=10, max_retries=5)`. If you build settings yourself, hand them over with `settings=`:

```python
from godaddy import GoDaddy, load_settings

settings = load_settings("/etc/myapp/godaddy.toml", environment="ote")
gd = GoDaddy(settings=settings)
```

### Endpoints

API paths are part of the settings too, so nothing is pinned in the code. Each one is a template relative to the base URL. `{version}` comes from `api_version`, and the other placeholders are filled in and URL encoded for each call.

| Name | Default |
| --- | --- |
| `domains` | `/{version}/domains` |
| `domain` | `/{version}/domains/{domain}` |
| `available` | `/{version}/domains/available` |
| `suggest` | `/{version}/domains/suggest` |
| `tlds` | `/{version}/domains/tlds` |
| `records` | `/{version}/domains/{domain}/records` |
| `records_by_type` | `/{version}/domains/{domain}/records/{type}` |
| `record` | `/{version}/domains/{domain}/records/{type}/{name}` |

You can override one of them in a config file:

```toml
[endpoints]
records = "/{version}/domains/{domain}/records"
```

or through the environment, with a double underscore between the parts:

```bash
export GODADDY_ENDPOINTS__TLDS="/{version}/domains/tlds"
```

GoDaddy gives you two environments. `production` is the default. `ote` is their test sandbox, and it needs its own keys.

Heads up: GoDaddy only opens the production Domains API to some account types. If every call comes back with `PermissionDeniedError`, check your account's API access first.

## DNS

Every DNS method takes the domain first. Record names are relative to the domain, and the apex is `@`.

```python
from godaddy import GoDaddy, DNSRecord

gd = GoDaddy()

gd.dns.list("example.com")
gd.dns.list("example.com", "A")
gd.dns.list("example.com", "A", "www")
gd.dns.get("example.com", "CNAME", "blog")
gd.dns.exists("example.com", "A", "shop")
```

Each of these returns a list of `DNSRecord` objects:

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=600, ...)
```

### Creating and changing records

```python
gd.dns.add(
    "example.com",
    DNSRecord.a("api", "203.0.113.20"),
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mail.example.com", priority=10),
)

gd.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)

gd.dns.delete("example.com", "A", "old")
gd.dns.delete("example.com", "A", "maybe-gone", missing_ok=True)
```

`add` appends records. `replace` swaps out every record with that type and name. Use `replace_type` to rewrite all records of one type, or `replace_all` to rewrite the whole zone. Be careful with `replace_all`: anything you leave out is removed.

### Shortcuts

```python
gd.dns.point("example.com", "shop", "203.0.113.10")
gd.dns.point("example.com", "shop", "2001:db8::10")
gd.dns.alias("example.com", "docs", "example.github.io")
gd.dns.set_txt("example.com", "_acme-challenge", "token-value", ttl=600)
gd.dns.unpoint("example.com", "shop")
```

`point` picks `A` or `AAAA` from the address you pass. `unpoint` deletes the record and does nothing if it is already gone.

### Example: one subdomain per customer

```python
from godaddy import GoDaddy, GoDaddyError

SERVER_IP = "203.0.113.10"

def create_customer_site(slug: str) -> str:
    with GoDaddy() as gd:
        if gd.dns.exists("example.com", "A", slug):
            raise ValueError(f"{slug}.example.com is already taken")
        gd.dns.point("example.com", slug, SERVER_IP)
    return f"{slug}.example.com"
```

## Domains

```python
for domain in gd.domains.iter():
    print(domain.domain, domain.expires, domain.renew_auto)

info = gd.domains.get("example.com")
info.name_servers

check = gd.domains.available("my-new-idea.com")
if check.available:
    print(check.price, check.currency)

gd.domains.available_many(["one.com", "two.net"])
gd.domains.suggest("coffee shop baku", limit=10)
gd.domains.tlds()

gd.domains.update("example.com", renew_auto=True, locked=True)
```

`available()` reports prices in normal currency units as a `Decimal`. GoDaddy itself sends them in micro units.

## Async

`AsyncGoDaddy` has the same methods. Await them.

```python
import asyncio
from godaddy import AsyncGoDaddy

async def main():
    async with AsyncGoDaddy() as gd:
        records = await gd.dns.list("example.com", "A")
        await gd.dns.point("example.com", "shop", "203.0.113.10")
        async for domain in gd.domains.iter():
            print(domain.domain)

asyncio.run(main())
```

## Errors

All exceptions inherit from `GoDaddyError`.

| Exception | When |
| --- | --- |
| `ValidationError` | 400 or 422, the request body or parameters were rejected |
| `AuthenticationError` | 401, or no credentials were found |
| `PermissionDeniedError` | 403 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `RateLimitError` | 429 that is still failing after retries. Has `.retry_after` |
| `ServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | the request never got an answer |

Status errors carry `status_code`, GoDaddy's `code`, a `fields` list that says which field failed and why, and the raw `response`.

```python
from godaddy import ValidationError

try:
    gd.dns.add("example.com", DNSRecord.a("bad name", "203.0.113.1"))
except ValidationError as exc:
    for field in exc.fields:
        print(field.path, field.message)
```

## Retries and timeouts

GoDaddy allows about 60 requests per minute. When it answers 429, the client waits as long as GoDaddy asks and tries again. Server errors and dropped connections are retried with exponential backoff, but only for idempotent methods (`GET`, `PUT`, `DELETE`). A `PATCH` that adds records is never sent twice.

```python
gd = GoDaddy(timeout=10, max_retries=5, max_retry_wait=30)
```

Set `max_retries=0` to turn retries off. To use proxies or a custom transport, pass your own `httpx.Client` or `httpx.AsyncClient` as `http_client=`.

Reseller accounts can act for a customer by passing `shopper_id=`.

## Messages

Every error and validation message the SDK produces is stored in `godaddy/messages.yaml`, so none of them are hardcoded. You can replace some or all of them, for example to translate them:

```yaml
value:
  empty_name: Record adı boş ola bilməz
error:
  timeout: "Sorğu vaxtı bitdi: {error}"
```

```python
from godaddy import messages

messages.use("messages.az.yaml")
messages.use({"value.empty_name": "Record adı boş ola bilməz"})
```

Unknown keys raise `KeyError`, which catches typos early. Call `messages.reset()` to go back to the defaults.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

The tests use `httpx.MockTransport`, so they never touch the real API.

## License

MIT
