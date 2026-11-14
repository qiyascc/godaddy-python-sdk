# Settings reference

Every setting the client reads, with its environment variable and default. Set them in code, in the environment or in a config file, as described in [](configuration.md).

| Setting | Environment variable | Type | Default | Allowed | Description |
| --- | --- | --- | --- | --- | --- |
| `api_key` | `GODADDY_API_KEY` | secret string | not set |  | API key from developer.godaddy.com/keys. |
| `api_secret` | `GODADDY_API_SECRET` | secret string | not set |  | API secret that belongs to the key. |
| `api_token` | `GODADDY_API_TOKEN` | secret string | not set |  | Personal access token (gd_pat_…). Used instead of the key and secret. |
| `environment` | `GODADDY_ENVIRONMENT` | string | `production` |  | Which GoDaddy environment to call: production or ote. |
| `base_url` | `GODADDY_BASE_URL` | string | not set |  | Full API URL. Overrides the environment when set. |
| `production_url` | `GODADDY_PRODUCTION_URL` | string | `https://api.godaddy.com` |  | API URL used for the production environment. |
| `ote_url` | `GODADDY_OTE_URL` | string | `https://api.ote-godaddy.com` |  | API URL used for the OTE test environment. |
| `api_version` | `GODADDY_API_VERSION` | string | `v1` |  | API version that fills the {version} part of every endpoint. |
| `endpoints` | `GODADDY_ENDPOINTS__<NAME>` | table | see below |  | Path templates for every API call, relative to the base URL. |
| `shopper_id` | `GODADDY_SHOPPER_ID` | string | not set |  | Customer shopper id for reseller calls, sent as X-Shopper-Id. |
| `timeout` | `GODADDY_TIMEOUT` | number | `30` | > 0 | Seconds to wait for a single request. |
| `max_retries` | `GODADDY_MAX_RETRIES` | integer | `3` | >= 0 | How many times a failed request is tried again. |
| `max_retry_wait` | `GODADDY_MAX_RETRY_WAIT` | number | `60` | >= 0 | Longest wait in seconds the client accepts from a rate limit answer. |
| `backoff_base` | `GODADDY_BACKOFF_BASE` | number | `0.5` | >= 0 | First backoff delay in seconds, doubled on every retry. |
| `backoff_cap` | `GODADDY_BACKOFF_CAP` | number | `8` | >= 0 | Longest backoff delay in seconds. |
| `page_size` | `GODADDY_PAGE_SIZE` | integer | `100` | >= 1, <= 1000 | Page size used when iterating over domains. |
| `user_agent` | `GODADDY_USER_AGENT` | string | `godaddy-python-sdk/{version}` |  | User-Agent header. {version} is replaced with the package version. |

## Endpoints

Each endpoint is a path template relative to the base URL. `{version}` is filled from `api_version`, the other placeholders from the call. Override one with `GODADDY_ENDPOINTS__<NAME>`, for example `GODADDY_ENDPOINTS__DOMAINS`.

| Name | Default |
| --- | --- |
| `endpoints.domains` | `/{version}/domains` |
| `endpoints.domain` | `/{version}/domains/{domain}` |
| `endpoints.available` | `/{version}/domains/available` |
| `endpoints.suggest` | `/{version}/domains/suggest` |
| `endpoints.tlds` | `/{version}/domains/tlds` |
| `endpoints.records` | `/{version}/domains/{domain}/records` |
| `endpoints.records_by_type` | `/{version}/domains/{domain}/records/{type}` |
| `endpoints.record` | `/{version}/domains/{domain}/records/{type}/{name}` |

## Files

Without `config_file=`, the client looks for these files in the working directory, in this order, and uses the first one it finds:

- `godaddy.toml`
- `godaddy.yaml`
- `godaddy.yml`
- `godaddy.json`

`GODADDY_CONFIG` points at a file anywhere else.
