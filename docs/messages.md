# Messages and translation

Every message the SDK produces, from "record name must not be empty" to "Request timed out", comes from one file: `godaddy/messages.yaml`. None of them are written into the code. That makes two things easy: translating them, and rewording them to fit your product.

## What is in the catalogue

The file has three sections:

| Section | What it holds |
| --- | --- |
| `settings` | The description of every setting. It shows up in goodconf's generated docs and in [](settings.md). |
| `error` | Messages for errors the SDK raises itself: missing credentials, timeouts, connection failures and similar. |
| `value` | Messages for `ValueError`s raised when you pass something that cannot be right, like an empty record name. |

Messages that come back from GoDaddy itself are passed through as they are. Only the SDK's own messages are in the catalogue.

You can see every key and its current text at runtime:

```python
from godaddy import messages

for key, value in sorted(messages.catalog().items()):
    print(key, "=", value)
```

## Overriding from a file

Write a YAML file with the same structure and only the keys you want to change. Placeholders in curly braces, like `{error}` or `{name!r}`, are filled in by the SDK, so keep them.

```yaml
value:
  empty_name: Record adı boş ola bilməz, kök üçün '@' yazın
  empty_domain: Domen adı boş ola bilməz
error:
  timeout: "Sorğunun vaxtı bitdi: {error}"
  connection: "Bağlantı alınmadı: {error}"
```

Load it once, early in your program:

```python
from godaddy import messages

messages.use("messages.az.yaml")
```

## Overriding from a dict

For one or two strings a dict is shorter. Use dotted keys or nested dicts, both work:

```python
messages.use({"value.empty_name": "Record adı boş ola bilməz"})
messages.use({"error": {"timeout": "Sorğunun vaxtı bitdi: {error}"}})
```

Overrides add up. Each `use()` call changes only the keys it mentions and keeps the rest.

## Typos are caught

A key that does not exist in the packaged catalogue raises `KeyError` and nothing is changed:

```python
messages.use({"value.empty_nmae": "..."})
```

```text
KeyError: 'value.empty_nmae'
```

## Going back to the defaults

```python
messages.reset()
```

The next message is read from the packaged file again.

## Scope

The catalogue is global to the process. Overrides apply to every client, sync and async, from the moment `use()` returns. If two parts of one program need different languages, translate at the edge of your application instead, for example by catching `GoDaddyError` and showing your own text.

```{note}
The `settings` texts are read once, when the package is imported, because they become the field descriptions of the `Settings` class. Overriding them later changes what `messages.catalog()` returns but not the descriptions already attached to `Settings`. The `error` and `value` texts are looked up every time a message is built, so overrides take effect at once.
```
