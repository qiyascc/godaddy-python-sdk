# Errors

Every exception the SDK raises on purpose inherits from {py:class}`~godaddy.GoDaddyError`, so one `except GoDaddyError` catches all API problems. Mistakes in your own arguments, like an empty record name or an invalid IP address, raise plain `ValueError` before any request is sent.

## The hierarchy

```text
GoDaddyError
├── APIConnectionError        the request never got an answer
│   └── APITimeoutError       it timed out
└── APIStatusError            GoDaddy answered with an error status
    ├── ValidationError       400, 422
    ├── AuthenticationError   401, or no credentials configured
    ├── PermissionDeniedError 403
    ├── NotFoundError         404
    ├── ConflictError         409
    ├── RateLimitError        429 after the retries ran out
    └── ServerError           500 and above
```

Any other 4xx status becomes a plain `APIStatusError`.

| Exception | Typical cause | What to do |
| --- | --- | --- |
| `ValidationError` | A field GoDaddy does not accept: a bad record value, a TTL out of range, an unknown status filter. | Read `exc.fields`, fix the input. Retrying will not help. |
| `AuthenticationError` | Wrong key or secret, a key for the other environment, or no credentials at all. | Check the key, the secret and `environment`. |
| `PermissionDeniedError` | The account is not allowed to use this API, or the key cannot touch this domain. | See [](credentials.md#production-access-is-limited). |
| `NotFoundError` | The domain is not in this account, or the record does not exist. | Check the spelling and the account. For deletes, consider `missing_ok=True`. |
| `ConflictError` | The change clashes with the current state. | Read the current records and try again with a change that fits. |
| `RateLimitError` | Too many requests, and waiting did not help within the retry budget. | Slow down, or raise `max_retries` and `max_retry_wait`. |
| `ServerError` | A problem on GoDaddy's side. | Try again later. Safe calls were already retried. |
| `APIConnectionError` | DNS failure, refused connection, broken TLS. | Check the network and any proxy. |
| `APITimeoutError` | No answer within `timeout`. | Raise `timeout`, or try again later. |

## What an error carries

All `GoDaddyError`s have:

| Attribute | Meaning |
| --- | --- |
| `message` | The message from GoDaddy, or from the SDK when there was no answer. |
| `status_code` | The HTTP status, or `None` for connection errors. |
| `code` | GoDaddy's own error code from the response body, for example `INVALID_BODY`. |
| `fields` | A list of {py:class}`~godaddy.FieldError` with `path`, `code` and `message` for each field GoDaddy rejected. |
| `response` | The raw `httpx.Response`, or `None`. |

`RateLimitError` also has `retry_after`, the number of seconds GoDaddy asked you to wait, taken from `retryAfterSec` in the body or the `Retry-After` header.

`str(exc)` puts it all on one line:

```text
[422] INVALID_BODY Request body doesn't fulfill schema (records[0].data: is not a valid IPv4 address)
```

## Handling patterns

### Show field errors to a user

```python
from godaddy import DNSRecord, GoDaddy, ValidationError

with GoDaddy() as gd:
    try:
        gd.dns.add("example.com", DNSRecord.txt("bad name", "value"))
    except ValidationError as exc:
        for field in exc.fields:
            print(f"{field.path}: {field.message}")
```

### Treat "not found" as normal

```python
from godaddy import NotFoundError

try:
    info = gd.domains.get(name)
except NotFoundError:
    info = None
```

For deletes there is a shorter way: `gd.dns.delete(domain, "A", "old", missing_ok=True)`.

### Separate your mistakes from theirs

```python
from godaddy import APIConnectionError, APIStatusError, GoDaddyError, ServerError

try:
    gd.dns.point("example.com", "shop", ip)
except ValueError:
    raise
except (ServerError, APIConnectionError):
    schedule_retry_later()
except APIStatusError as exc:
    log.error("GoDaddy refused the change: %s", exc)
    raise
```

`ValueError` means the call was never sent. `ServerError` and `APIConnectionError` are worth trying again later. Other status errors need a change in the request.

### Log enough to debug

```python
try:
    gd.dns.point("example.com", "shop", ip)
except GoDaddyError as exc:
    log.error(
        "GoDaddy call failed: status=%s code=%s message=%s",
        exc.status_code, exc.code, exc.message,
    )
    raise
```

`exc.response.request` holds the request that failed, including the URL. Do not log its headers: they contain your key and secret.

## Errors raised before a request

| Error | When |
| --- | --- |
| `AuthenticationError` | Building a client with no key pair and no token anywhere. |
| `ValueError` | `environment` is not `production`, `prod`, `ote` or `test`. |
| `ValueError` | An empty domain, name or type, an invalid IP address, `add()` with no records, `replace()` with no values, `available_many([])`, `update()` with nothing to change, or a `replace_type()` record of the wrong type. |
| `pydantic.ValidationError` | A setting outside its range, for example `timeout=0` or `max_retries=-1`. |

The texts of the SDK's own messages can be changed or translated, see [](messages.md).
