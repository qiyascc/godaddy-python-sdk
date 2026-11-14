# Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf). You can set any of them in three places, and mix them freely:

1. **In code**, as keyword arguments to `GoDaddy(...)`.
2. **In the environment**, as `GODADDY_*` variables.
3. **In a config file**: TOML, YAML or JSON.

When the same setting is in more than one place, code wins over the environment, and the environment wins over the file. Anything you do not set keeps its default. The full list is on [](settings.md).

## In code

The first two positional arguments are the key and the secret. Everything else is a keyword argument with the same name as the setting:

```python
from godaddy import GoDaddy

gd = GoDaddy(
    "API_KEY",
    "API_SECRET",
    environment="ote",
    timeout=10,
    max_retries=5,
)
```

Passing `None` for a setting is the same as not passing it, so the next source (environment or file) is used.

## In the environment

Every setting has a variable named `GODADDY_` plus the setting name in capitals:

```bash
export GODADDY_API_KEY=your-key
export GODADDY_API_SECRET=your-secret
export GODADDY_ENVIRONMENT=production
export GODADDY_TIMEOUT=15
export GODADDY_MAX_RETRIES=3
```

Nested settings, the endpoint paths, use a double underscore between the parts:

```bash
export GODADDY_ENDPOINTS__RECORDS="/{version}/domains/{domain}/records"
```

This style suits servers, containers and CI, where secrets usually arrive as environment variables anyway.

## In a config file

With no arguments, the client looks in the current working directory for, in this order:

1. `godaddy.toml`
2. `godaddy.yaml`
3. `godaddy.yml`
4. `godaddy.json`

To load a file from somewhere else, set `GODADDY_CONFIG` or pass `config_file=`:

```bash
export GODADDY_CONFIG=/etc/myapp/godaddy.toml
```

```python
gd = GoDaddy(config_file="/etc/myapp/godaddy.toml")
```

::::{tab-set}

:::{tab-item} TOML
```toml
api_key = "your-key"
api_secret = "your-secret"
environment = "production"
timeout = 15
max_retries = 3

[endpoints]
records = "/{version}/domains/{domain}/records"
```
:::

:::{tab-item} YAML
```yaml
api_key: your-key
api_secret: your-secret
environment: production
timeout: 15
max_retries: 3
endpoints:
  records: /{version}/domains/{domain}/records
```
:::

:::{tab-item} JSON
```json
{
  "api_key": "your-key",
  "api_secret": "your-secret",
  "environment": "production",
  "timeout": 15,
  "max_retries": 3,
  "endpoints": {"records": "/{version}/domains/{domain}/records"}
}
```
:::
::::

YAML needs the `yaml` extra. TOML needs the `toml` extra on Python 3.10, while 3.11 and newer read it on their own. JSON always works. See [](installation.md#optional-extras).

Unknown keys in a file or in the environment are ignored, so a shared config file can hold settings for other tools too.

```{warning}
A config file with a key in it is a secret. Add it to `.gitignore` and give it tight file permissions on servers, for example `chmod 600 godaddy.toml`.
```

## Building settings yourself

`load_settings()` returns the same `Settings` object the client builds internally. That is handy when one process creates several clients, or when you want to look at the resolved values first:

```python
from godaddy import GoDaddy, load_settings

settings = load_settings("/etc/myapp/godaddy.toml", environment="ote")
print(settings.environment, settings.resolved_base_url())

gd = GoDaddy(settings=settings)
```

The first argument is the config file path (or `None` to use the default lookup). Keyword arguments override the file and the environment, exactly like arguments to `GoDaddy(...)`.

If you pass `settings=` and other arguments together, the arguments are applied on top of a copy of the settings:

```python
gd = GoDaddy(settings=settings, timeout=5)
```

## Environments and base URL

`environment` picks the API host: `production` (alias `prod`) or `ote` (alias `test`). The hosts come from `production_url` and `ote_url`. `base_url`, when set, beats all of them, which is how you send requests through a proxy or a recording server:

```python
gd = GoDaddy(base_url="http://localhost:8080")
```

## API version and endpoints

GoDaddy's paths start with an API version. `api_version` (default `v1`) fills the `{version}` part of every path. Each endpoint is a template relative to the base URL, and other placeholders such as `{domain}` are URL encoded and filled in for every call.

| Name | Default | Used by |
| --- | --- | --- |
| `domains` | `/{version}/domains` | `domains.list`, `domains.iter` |
| `domain` | `/{version}/domains/{domain}` | `domains.get`, `domains.update` |
| `available` | `/{version}/domains/available` | `domains.available`, `domains.available_many` |
| `suggest` | `/{version}/domains/suggest` | `domains.suggest` |
| `tlds` | `/{version}/domains/tlds` | `domains.tlds` |
| `records` | `/{version}/domains/{domain}/records` | `dns.list` without a type, `dns.add`, `dns.replace_all` |
| `records_by_type` | `/{version}/domains/{domain}/records/{type}` | `dns.list` with a type, `dns.replace_type` |
| `record` | `/{version}/domains/{domain}/records/{type}/{name}` | `dns.list` with a type and name, `dns.get`, `dns.exists`, `dns.replace`, `dns.delete` |

You only need to touch these if GoDaddy moves a path before the SDK catches up, or if a gateway in front of the API rewrites paths. Override one and the others keep their defaults.

## User agent

Every request carries `User-Agent: godaddy-python-sdk/<version>`. Change it with `user_agent`. The text `{version}` is replaced with the package version:

```python
gd = GoDaddy(user_agent="acme-dns-bot/2.1 (godaddy-python-sdk/{version})")
```

## Reading the active settings

The client keeps the settings it used:

```python
gd = GoDaddy()
print(gd)
print(gd.settings.timeout, gd.settings.max_retries)
```

```text
GoDaddy(environment='production', base_url='https://api.godaddy.com')
30.0 3
```

Secrets stay hidden when printed: `gd.settings.api_secret` shows as `SecretStr('**********')`.
