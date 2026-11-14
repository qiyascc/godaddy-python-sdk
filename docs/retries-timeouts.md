# Retries and timeouts

Networks drop packets and APIs have bad minutes. The SDK retries the failures that are worth retrying, and only when a retry cannot do harm.

## What is retried

| Failure | Retried? | How long it waits |
| --- | --- | --- |
| `429 Too Many Requests` | Yes, for every method. | As long as GoDaddy asks (`retryAfterSec` in the body or the `Retry-After` header), if that is within `max_retry_wait`. Without a hint, exponential backoff. |
| `500`, `502`, `503`, `504` | Only for `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Timeout or connection error | Only for `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Any other status | No. | |

`PATCH` and `POST` are never retried after a server error or a dropped connection, because the first attempt may have reached GoDaddy. In this SDK that means `dns.add`, `domains.update` and `domains.available_many`. A rate limit answer is different: GoDaddy refused the request without doing it, so it is safe to send again.

When the retries run out, the last error is raised: `RateLimitError`, `ServerError`, `APITimeoutError` or `APIConnectionError`.

## The settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `max_retries` | `3` | Retries after the first attempt. `0` turns retries off. |
| `max_retry_wait` | `60` | The longest wait, in seconds, the client accepts from a rate limit answer. If GoDaddy asks for more, the client gives up at once and raises `RateLimitError`. |
| `backoff_base` | `0.5` | First backoff delay in seconds. It doubles on every retry. |
| `backoff_cap` | `8` | Upper limit for one backoff delay. |
| `timeout` | `30` | Seconds to wait for one request. Applies to the HTTP client the SDK creates. |

```python
gd = GoDaddy(timeout=10, max_retries=5, max_retry_wait=30)
```

## How the backoff is computed

For retry number `n` (starting at 0) the wait is:

```text
min(backoff_cap, backoff_base * 2 ** n) + random(0, backoff_base / 2)
```

With the defaults that is about 0.5, 1, 2, 4 and then 8 seconds, plus a little random jitter so many clients that failed together do not all come back at the same moment.

## GoDaddy's rate limit

GoDaddy allows about 60 requests per minute. A script that changes hundreds of records will hit that limit. The client waits and carries on by itself, but a long batch job is smoother if it spaces its calls out:

```python
import time

for name, ip in many_records:
    gd.dns.point("example.com", name, ip)
    time.sleep(1.1)
```

Better still, change many records in one call. `replace_type` and `replace_all` write whole sets in a single request.

## Turning retries off

In tests, or when a caller of yours already retries, set `max_retries=0`:

```python
gd = GoDaddy(max_retries=0)
```

Every failure is then raised at once.

## Timeouts in detail

`timeout` is passed to the `httpx.Client` the SDK creates, and covers connecting, sending and reading. A timed out `GET`, `PUT` or `DELETE` is retried like a connection error. If you pass your own client with `http_client=`, its timeout is used instead, see [](http-client.md).
