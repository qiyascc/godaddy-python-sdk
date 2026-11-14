# API reference

This page lists every public class and function with its signature. The guides explain how to use them: [](dns.md), [](domains.md), [](errors.md) and [](configuration.md).

Everything below can be imported straight from `godaddy`, except the resource classes, which you reach through a client (`gd.dns`, `gd.domains`).

## Clients

`GoDaddy` is the sync client and `AsyncGoDaddy` the async one. Both take the same arguments:

| Argument | Meaning |
| --- | --- |
| `api_key`, `api_secret` | The key pair. Positional. A `gd_pat_` value as `api_key` with no secret is used as a token. |
| `settings` | A ready `Settings` object. Other arguments are applied on top of it. |
| `config_file` | Path to a TOML, YAML or JSON settings file. |
| `http_client` | Your own `httpx.Client` (sync) or `httpx.AsyncClient` (async). |
| any setting | For example `environment="ote"`, `timeout=10`, `api_token="gd_pat_..."`. See [](settings.md). |

Each client has two attributes for the API areas, `dns` and `domains`, plus `settings`, `base_url` and `environment`.

```{eval-rst}
.. autoclass:: godaddy.GoDaddy
   :members:
   :inherited-members:
   :exclude-members: settings

.. autoclass:: godaddy.AsyncGoDaddy
   :members:
   :inherited-members:
   :exclude-members: settings
```

## What the methods return

The resource methods are annotated as returning `Any`, because one implementation serves both clients: on `GoDaddy` they return the value, on `AsyncGoDaddy` a coroutine that resolves to it. These are the values:

| Method | Returns |
| --- | --- |
| `dns.list`, `dns.get` | `list[DNSRecord]` |
| `dns.exists` | `bool` |
| `dns.add`, `dns.replace`, `dns.replace_type`, `dns.replace_all`, `dns.delete` | `None` |
| `dns.point`, `dns.unpoint`, `dns.alias`, `dns.set_txt` | `None` |
| `domains.list` | `list[Domain]` |
| `domains.iter` | iterator of `Domain` (async iterator on the async client) |
| `domains.get` | `Domain` |
| `domains.available` | `Availability` |
| `domains.available_many` | `list[Availability]` |
| `domains.suggest` | `list[Suggestion]` |
| `domains.tlds` | `list[Tld]` |
| `domains.update` | `None` |

## DNS

Reached as `gd.dns`. The async client has `AsyncDNS` with the same methods as coroutines.

```{eval-rst}
.. autoclass:: godaddy.resources.DNS
   :members:

.. autoclass:: godaddy.resources.AsyncDNS
   :members:
```

## Domains

Reached as `gd.domains`. `Domains.iter` is a generator, `AsyncDomains.iter` an async generator. The other methods are shared.

```{eval-rst}
.. autoclass:: godaddy.resources.Domains
   :members:
   :inherited-members:

.. autoclass:: godaddy.resources.AsyncDomains
   :members:
   :inherited-members:
```

## Models

Dataclasses returned by the API calls. Fields are described in the guides.

```{eval-rst}
.. autoclass:: godaddy.DNSRecord
   :members:

.. autoclass:: godaddy.RecordType
   :members:
   :undoc-members:

.. autoclass:: godaddy.Domain
   :members:

.. autoclass:: godaddy.Contact
   :members:

.. autoclass:: godaddy.Availability
   :members:

.. autoclass:: godaddy.Suggestion
   :members:

.. autoclass:: godaddy.Tld
   :members:
```

## Settings

```{eval-rst}
.. autofunction:: godaddy.load_settings

.. autoclass:: godaddy.Settings
   :members: resolved_base_url, path, resolved_user_agent
   :exclude-members: authorization
```

## Errors

```{eval-rst}
.. autoexception:: godaddy.GoDaddyError
.. autoexception:: godaddy.APIConnectionError
.. autoexception:: godaddy.APITimeoutError
.. autoexception:: godaddy.APIStatusError
.. autoexception:: godaddy.ValidationError
.. autoexception:: godaddy.AuthenticationError
.. autoexception:: godaddy.PermissionDeniedError
.. autoexception:: godaddy.NotFoundError
.. autoexception:: godaddy.ConflictError
.. autoexception:: godaddy.RateLimitError
.. autoexception:: godaddy.ServerError
.. autoclass:: godaddy.FieldError
   :members:
```

## Messages

```{eval-rst}
.. automodule:: godaddy.messages
   :members: use, reset, catalog, text
```
