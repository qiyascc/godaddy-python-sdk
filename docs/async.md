# Async

`AsyncGoDaddy` is the async twin of `GoDaddy`. It takes the same arguments, reads the same settings and has the same methods with the same parameters. The only difference is that every call that talks to the API is a coroutine you `await`.

## A first async script

```python
import asyncio

from godaddy import AsyncGoDaddy


async def main() -> None:
    async with AsyncGoDaddy() as gd:
        records = await gd.dns.list("example.com", "A")
        for record in records:
            print(record.name, record.data)

        await gd.dns.point("example.com", "shop", "203.0.113.10")


asyncio.run(main())
```

`async with` closes the underlying `httpx.AsyncClient` when the block ends. Without it, call `await gd.close()` yourself.

## Iterating

`domains.iter()` is an async generator on the async client. Use `async for`:

```python
async with AsyncGoDaddy() as gd:
    async for domain in gd.domains.iter():
        print(domain.domain)
```

Everything else returns a plain value once awaited: `await gd.dns.list(...)` is a `list[DNSRecord]`.

## Running calls side by side

Because the client is async, several requests can be in flight at once. `asyncio.gather` is the simplest way:

```python
import asyncio

from godaddy import AsyncGoDaddy

SUBDOMAINS = {"shop": "203.0.113.10", "blog": "203.0.113.11", "api": "203.0.113.12"}


async def main() -> None:
    async with AsyncGoDaddy() as gd:
        await asyncio.gather(*(
            gd.dns.point("example.com", name, ip) for name, ip in SUBDOMAINS.items()
        ))


asyncio.run(main())
```

Each `point` writes a different name with its own `PUT`, so the calls do not interfere with each other. Keep GoDaddy's rate limit of about 60 requests per minute in mind when you start many at once. The client waits and retries on `429`, but it is kinder to limit concurrency yourself.

To cap how many requests run at the same time, wrap the calls in a semaphore:

```python
limit = asyncio.Semaphore(3)


async def point(client, name: str, ip: str) -> None:
    async with limit:
        await client.dns.point("example.com", name, ip)
```

## Using it from a web framework

Create one client when the application starts and close it when it stops, instead of building a new one per request. Each client holds a connection pool, and reusing it saves a TLS handshake on every call. [](examples/web-frameworks.md) shows this for FastAPI.

## Mixing sync and async

Do not call the sync `GoDaddy` from inside a running event loop, because it blocks the loop while it waits for GoDaddy. In async code, use `AsyncGoDaddy`. In sync code that needs a one off async call, `asyncio.run()` is fine.

## Errors and retries

The async client raises the same exceptions as the sync one (see [](errors.md)) and retries the same way (see [](retries-timeouts.md)). While it waits between retries it uses `asyncio.sleep`, so other tasks keep running.
