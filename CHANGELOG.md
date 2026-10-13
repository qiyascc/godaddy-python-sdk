# Changelog

## 0.1.0

First release.

- Sync `GoDaddy` and async `AsyncGoDaddy` clients
- DNS: list, get, exists, add, replace, replace_type, replace_all, delete
- DNS shortcuts: point, unpoint, alias, set_txt
- Domains: list, iter, get, available, available_many, suggest, tlds, update
- Typed errors, with automatic retries for rate limits and server errors
- Configuration through goodconf: code, `GODADDY_*` environment variables or a TOML, YAML or JSON file
- Every user facing message lives in `messages.json` and can be overridden at runtime
