# Django and FastAPI

Web applications usually create DNS records as a side effect of something a user does: signing up, adding a custom domain, launching a site. This page shows a clean way to do it in Django (sync) and FastAPI (async).

The rule in both: **create one client per process and reuse it**. A client holds a pool of open connections, so building a new one per request throws away the TLS handshake every time.

## Django

### Settings

Keep the credentials in the environment, not in `settings.py`. The SDK reads the `GODADDY_*` variables on its own. Add only what belongs to your app:

```python
SITE_ZONE = "example.com"
SITE_SERVER_IP = "203.0.113.10"
```

### A shared client

`customers/dns.py`:

```python
from functools import lru_cache

from godaddy import GoDaddy


@lru_cache(maxsize=1)
def dns_client() -> GoDaddy:
    return GoDaddy()
```

The first call builds the client, later calls in the same process get the same one. Under gunicorn or uWSGI each worker process gets its own, which is what you want.

### The model and the view

```python
from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from godaddy import GoDaddyError

from .dns import dns_client


class CustomerSite(models.Model):
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


@require_POST
def create_site(request):
    slug = request.POST["slug"].lower()
    try:
        with transaction.atomic():
            site = CustomerSite.objects.create(slug=slug)
            dns_client().dns.point(settings.SITE_ZONE, site.slug, settings.SITE_SERVER_IP)
    except IntegrityError:
        return JsonResponse({"error": f"{slug} is already taken"}, status=409)
    except GoDaddyError as exc:
        return JsonResponse({"error": f"DNS update failed: {exc.message}"}, status=502)
    return JsonResponse({"host": f"{slug}.{settings.SITE_ZONE}"}, status=201)
```

The `unique=True` on `slug` stops two requests from claiming the same name, even if they arrive at the same moment: the second one gets an `IntegrityError` and a 409. The DNS call runs inside the transaction: if GoDaddy refuses, the exception rolls the row back, so the database and DNS do not drift apart.

### Moving it out of the request

A DNS call takes a few hundred milliseconds, and much longer if the client has to wait out a rate limit. For anything beyond a small admin tool, run it in a background worker (Celery, RQ, django-q2 or similar) and let the request return at once:

```python
def create_dns_record(slug: str) -> None:
    dns_client().dns.point(settings.SITE_ZONE, slug, settings.SITE_SERVER_IP)
```

Queue `create_dns_record` after the row is committed, for example with `transaction.on_commit`.

## FastAPI

Use the async client and tie its life to the application with a lifespan handler:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from godaddy import AsyncGoDaddy, GoDaddyError

ZONE = "example.com"
SERVER_IP = "203.0.113.10"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncGoDaddy() as client:
        app.state.dns = client
        yield


app = FastAPI(lifespan=lifespan)


class NewSite(BaseModel):
    slug: str


@app.post("/sites", status_code=201)
async def create_site(body: NewSite, request: Request):
    client = request.app.state.dns
    if await client.dns.exists(ZONE, "A", body.slug):
        raise HTTPException(409, f"{body.slug}.{ZONE} is taken")
    try:
        await client.dns.point(ZONE, body.slug, SERVER_IP)
    except GoDaddyError as exc:
        raise HTTPException(502, f"DNS update failed: {exc.message}") from exc
    return {"host": f"{body.slug}.{ZONE}"}


@app.delete("/sites/{slug}", status_code=204)
async def delete_site(slug: str, request: Request):
    await request.app.state.dns.dns.unpoint(ZONE, slug)
```

The client is created once when the app starts and closed when it shuts down. Because it is async, a slow answer from GoDaddy does not block other requests.

Validate `slug` before it reaches DNS, as shown in [](customer-subdomains.md).

## Errors to show users

Turn SDK errors into messages a user can act on, and keep the details in your logs:

| Exception | Answer |
| --- | --- |
| `ValueError` | 400: the name is not valid. |
| `NotFoundError` | 500: your zone setting is wrong, this is your bug. |
| `RateLimitError` | 503: try again in a minute. |
| `ServerError`, `APIConnectionError` | 502: the DNS provider is having trouble. |
| other `GoDaddyError` | 502, and log `exc` in full. |
