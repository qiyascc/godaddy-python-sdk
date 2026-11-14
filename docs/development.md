# Development

The SDK is a small codebase and contributions are welcome: bug reports, fixes, new endpoints or better docs.

## Get the code

```bash
git clone https://github.com/qiyascc/godaddy-python-sdk.git
cd godaddy-python-sdk
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows CMD, activate with `.venv\Scripts\activate.bat` instead.

The `dev` extra installs the package in editable mode with the TOML and YAML extras, pytest, pytest-asyncio, ruff, mypy and the PyYAML type stubs.

## Project layout

```text
src/godaddy/
    __init__.py        public names
    client.py          GoDaddy and AsyncGoDaddy
    _base.py           request loop, retries, sync and async transports
    config.py          Settings and load_settings
    errors.py          exception classes and status mapping
    models.py          dataclasses returned by the API calls
    messages.py        message catalogue loader
    messages.yaml      every user facing message
    resources/         one module per API area
tests/                 pytest suite, runs against httpx.MockTransport
examples/              small runnable scripts and a sample config file
docs/                  this documentation
```

## Run the tests

```bash
pytest
```

The tests use `httpx.MockTransport`, so they never touch the real API and need no credentials. Async tests run through pytest-asyncio in auto mode.

## Lint and type check

```bash
ruff check .
mypy src
```

## Build the docs

```bash
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. `-W` turns warnings into errors, the same way Read the Docs builds it.

## Making a change

1. Open an issue first for anything larger than a small fix, so we can agree on the shape.
2. Add or update tests next to the code you change.
3. Keep user facing text in `messages.yaml`, not in the code.
4. Run `pytest` and `ruff check .` before you push.
5. Describe what changed and why in the pull request.

## Reporting a bug

Open an issue at [github.com/qiyascc/godaddy-python-sdk/issues](https://github.com/qiyascc/godaddy-python-sdk/issues) with the SDK version (`godaddy.__version__`), your Python version, the call you made and the full exception. Remove your credentials from anything you paste.
