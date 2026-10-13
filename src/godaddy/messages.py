from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]

_PACKAGE_FILE = "messages.json"
_catalog: dict[str, str] = {}


def _read_packaged() -> dict[str, str]:
    raw = resources.files(__package__).joinpath(_PACKAGE_FILE).read_text(encoding="utf-8")
    return dict(json.loads(raw))


def catalog() -> Mapping[str, str]:
    if not _catalog:
        _catalog.update(_read_packaged())
    return _catalog


def use(source: PathLike | Mapping[str, str]) -> None:
    if isinstance(source, Mapping):
        overrides = dict(source)
    else:
        overrides = dict(json.loads(Path(source).read_text(encoding="utf-8")))
    unknown = set(overrides) - set(_read_packaged())
    if unknown:
        raise KeyError(", ".join(sorted(unknown)))
    catalog()
    _catalog.update(overrides)


def reset() -> None:
    _catalog.clear()


def text(key: str, **params: Any) -> str:
    template = catalog()[key]
    return template.format(**params) if params else template
