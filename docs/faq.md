# FAQ and troubleshooting

## Every call fails with `PermissionDeniedError`

The key works, but GoDaddy does not let this account use the production Domains API. GoDaddy limits it to some account types. Check the API access rules for your account on the developer portal. OTE keys are not affected, so you can keep developing against `environment="ote"` in the meantime.

## `AuthenticationError: Missing credentials`

The client found no key pair and no token. It looked at the arguments, the `GODADDY_*` environment variables and the config files listed on [](settings.md#files). Common causes:

- The variables were exported in a different terminal, or a service does not inherit your shell's environment.
- `godaddy.toml` is in another folder than the one the script runs from. Set `GODADDY_CONFIG` to its full path.
- Only the key is set, not the secret.

## `AuthenticationError` with a 401 status

GoDaddy rejected the credentials. Check that the key belongs to the environment you call. OTE keys do not work in production and the other way round.

## My change does not show up in `nslookup`

The API call succeeded, but resolvers cache answers for the record's TTL. Wait for the old TTL to pass. Also check that the domain actually uses GoDaddy's name servers: `gd.domains.get("example.com").name_servers`. If they point elsewhere, the zone at GoDaddy is not the one the internet sees.

## `NotFoundError` when deleting a record

GoDaddy answers 404 when there is nothing to delete. Pass `missing_ok=True` to treat that as success, or use `unpoint` for `A` and `AAAA` records, which already does.

## How do I set the apex record?

Use `@` as the name: `gd.dns.point("example.com", "@", "203.0.113.10")`.

## How do I add a second `A` record without removing the first?

`replace` and `point` replace the whole set. To keep what is there, either pass all the values to `replace`:

```python
current = [r.data for r in gd.dns.list("example.com", "A", "www")]
gd.dns.replace("example.com", "A", "www", current + ["203.0.113.11"])
```

or use `add`:

```python
gd.dns.add("example.com", DNSRecord.a("www", "203.0.113.11"))
```

## Can I set a TTL lower than 600?

The SDK sends what you pass. GoDaddy decides what it accepts and answers with `ValidationError` if the value is out of range.

## Why are prices `Decimal` and not `float`?

Money should not be rounded by binary floating point. GoDaddy sends prices in micro units and the SDK converts them exactly.

## The script hangs for a while and then works

That is the rate limit at work. GoDaddy answered 429 and the client is waiting before it tries again. Lower your request rate, or see [](retries-timeouts.md) to change how long it may wait.

## Can I call endpoints the SDK does not wrap?

Not through a public method. The clients only expose the Domains and DNS calls documented here. For other GoDaddy APIs, use httpx directly with the same `Authorization` header: `gd.settings.authorization()` returns it.

## Is the client thread safe?

The sync client wraps an `httpx.Client`, which can be shared between threads. The SDK keeps no state that changes between calls. Still, the simplest safe setup is one client per thread or one per process.

## How do I see what is sent?

Pass an `httpx.Client` with event hooks, as shown in [](http-client.md#logging-every-request).
