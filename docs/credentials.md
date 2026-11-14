# API keys and environments

Every request to GoDaddy carries credentials. The SDK supports both kinds GoDaddy hands out: a key pair (a key and a secret) and a personal access token.

## Create a key pair

1. Sign in at [developer.godaddy.com/keys](https://developer.godaddy.com/keys) with the GoDaddy account that owns the domains.
2. Create a new API key and pick the environment it is for: **Production** or **OTE** (GoDaddy's test environment).
3. Copy the **key** and the **secret** and keep them somewhere safe. If the secret leaks or gets lost, delete the key and create a new one.

The SDK sends a key pair as:

```text
Authorization: sso-key <key>:<secret>
```

```python
from godaddy import GoDaddy

gd = GoDaddy("API_KEY", "API_SECRET")
```

## Use a personal access token

GoDaddy also issues personal access tokens that start with `gd_pat_`. The SDK sends them as a bearer token:

```text
Authorization: Bearer gd_pat_...
```

There are three ways to pass one:

```python
gd = GoDaddy(api_token="gd_pat_...")
gd = GoDaddy("gd_pat_...")
```

```bash
export GODADDY_API_TOKEN=gd_pat_...
```

The second form works because a value that starts with `gd_pat_`, passed as the key with no secret, is treated as a token. When both a token and a key pair are set, the token wins.

## Production and OTE

GoDaddy runs two separate environments:

| Environment | `environment=` | Base URL | What it is for |
| --- | --- | --- | --- |
| Production | `production` (or `prod`) | `https://api.godaddy.com` | Your real domains. Changes go live. |
| OTE | `ote` (or `test`) | `https://api.ote-godaddy.com` | GoDaddy's test sandbox. Nothing you do there touches real DNS. |

Production is the default. OTE needs its own keys: a key made for OTE does not work against production, and a production key does not work against OTE.

```python
gd = GoDaddy("OTE_KEY", "OTE_SECRET", environment="ote")
```

Any other value for `environment` raises `ValueError` when the client is built. If you need a different URL altogether, for example a proxy in front of the API, set `base_url`. It overrides the environment.

## Production access is limited

GoDaddy only opens the production Domains API to some account types. If every call comes back with `PermissionDeniedError` (HTTP 403) even though the key is correct, the account itself is not allowed to use the API. Check the API access requirements on GoDaddy's developer portal for your account before you look for a bug in your code.

## Reseller accounts

A reseller can act for one of its customers by sending the customer's shopper id. Set `shopper_id` and the SDK adds the `X-Shopper-Id` header to every request:

```python
gd = GoDaddy("RESELLER_KEY", "RESELLER_SECRET", shopper_id="123456789")
```

## Where to keep the secret

Keep keys out of your source code and out of git.

- In development, an environment variable or a `godaddy.toml` file that is listed in `.gitignore` works well.
- On a server, use the environment of the service (a systemd `EnvironmentFile`, a container secret, your platform's secret store).
- In CI, use the CI system's secret variables.

The settings store the key, secret and token as pydantic `SecretStr`, so printing the settings object shows `**********` instead of the value.

## Check that the credentials work

The cheapest read call lists one domain:

```python
from godaddy import GoDaddy, AuthenticationError, PermissionDeniedError

with GoDaddy() as gd:
    try:
        domains = gd.domains.list(limit=1)
    except AuthenticationError:
        print("GoDaddy rejected the key or secret")
    except PermissionDeniedError:
        print("The key is valid but this account cannot use the API")
    else:
        print("Credentials work,", len(domains), "domain(s) returned")
```

If no credentials are found anywhere, building the client raises `AuthenticationError` with a message that lists every place the SDK looked.
