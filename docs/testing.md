# Testing your code

Code that changes DNS should be tested without touching real DNS. The SDK accepts any `httpx` client, so you can plug in `httpx.MockTransport` and decide in your test what "GoDaddy" answers. This is how the SDK's own test suite works.

## A minimal fake GoDaddy

```python
import httpx

from godaddy import GoDaddy


def fake_godaddy(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/v1/domains/example.com/records/A/shop":
        return httpx.Response(200, json=[{"type": "A", "name": "shop", "data": "203.0.113.10", "ttl": 600}])
    return httpx.Response(200, json=[])


http = httpx.Client(transport=httpx.MockTransport(fake_godaddy))
gd = GoDaddy("test-key", "test-secret", http_client=http)

print(gd.dns.list("example.com", "A", "shop"))
```

No request leaves the machine. The key and secret can be anything, since only your handler sees them.

## A recorder fixture for pytest

Most tests want two things: queue the answers GoDaddy should give, then check what was sent. A small recorder class does both:

```python
import json

import httpx
import pytest

from godaddy import GoDaddy


class Recorder:
    def __init__(self):
        self.requests = []
        self.responses = []

    def queue(self, status=200, body=None, headers=None):
        content = b"" if body is None else json.dumps(body).encode()
        self.responses.append(httpx.Response(status, content=content, headers=headers or {}))

    def __call__(self, request):
        self.requests.append(request)
        if not self.responses:
            return httpx.Response(200, content=b"[]")
        return self.responses.pop(0)

    @property
    def last(self):
        return self.requests[-1]


@pytest.fixture
def api():
    return Recorder()


@pytest.fixture
def gd(api):
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = GoDaddy("key", "secret", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client
```

The last line makes retries instant, so a test of the retry path does not sleep. `_wait_for` is internal, so keep this trick inside tests.

## Example tests

Test your own function, not the SDK. Here the code under test gives each customer a subdomain:

```python
from godaddy import GoDaddy


def create_customer_site(gd: GoDaddy, slug: str) -> str:
    if gd.dns.exists("example.com", "A", slug):
        raise ValueError(f"{slug}.example.com is already taken")
    gd.dns.point("example.com", slug, "203.0.113.10")
    return f"{slug}.example.com"
```

```python
import json

import pytest


def test_creates_the_record(gd, api):
    api.queue(200, [])
    api.queue(200)

    assert create_customer_site(gd, "acme") == "acme.example.com"

    assert api.last.method == "PUT"
    assert api.last.url.path == "/v1/domains/example.com/records/A/acme"
    assert json.loads(api.last.content) == [{"data": "203.0.113.10", "ttl": 600}]


def test_refuses_a_taken_name(gd, api):
    api.queue(200, [{"type": "A", "name": "acme", "data": "198.51.100.1", "ttl": 600}])

    with pytest.raises(ValueError):
        create_customer_site(gd, "acme")
    assert len(api.requests) == 1
```

## Testing error handling

Queue an error answer the way GoDaddy sends it:

```python
from godaddy import ValidationError


def test_shows_field_errors(gd, api):
    api.queue(422, {
        "code": "INVALID_BODY",
        "message": "Request body doesn't fulfill schema",
        "fields": [{"path": "records[0].data", "code": "INVALID", "message": "bad address"}],
    })

    with pytest.raises(ValidationError) as caught:
        gd.dns.replace("example.com", "A", "www", "203.0.113.10")

    assert caught.value.fields[0].path == "records[0].data"
```

And a rate limit that clears up after one retry:

```python
def test_waits_out_a_rate_limit(gd, api):
    api.queue(429, {"code": "TOO_MANY_REQUESTS", "retryAfterSec": 1})
    api.queue(200, [])

    assert gd.dns.list("example.com", "A") == []
    assert len(api.requests) == 2
```

## Async tests

The same recorder works with `httpx.AsyncClient`. With pytest-asyncio installed:

```python
import httpx
import pytest

from godaddy import AsyncGoDaddy


@pytest.fixture
def agd(api):
    http = httpx.AsyncClient(transport=httpx.MockTransport(api))
    client = AsyncGoDaddy("key", "secret", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


@pytest.mark.asyncio
async def test_async_point(agd, api):
    api.queue(200)
    await agd.dns.point("example.com", "shop", "203.0.113.10")
    assert api.last.method == "PUT"
```

## Testing against OTE

For an end to end check before a release, run a few tests against GoDaddy's OTE environment with OTE keys. Keep those tests out of the normal suite, for example behind a marker, so they only run when you ask:

```python
import os

import pytest

from godaddy import GoDaddy

pytestmark = pytest.mark.skipif("GODADDY_OTE_KEY" not in os.environ, reason="no OTE key")


def test_ote_roundtrip():
    with GoDaddy(os.environ["GODADDY_OTE_KEY"], os.environ["GODADDY_OTE_SECRET"], environment="ote") as gd:
        gd.domains.list(limit=1)
```
