from __future__ import annotations

import json

import pytest

from godaddy import messages


@pytest.fixture(autouse=True)
def restore():
    yield
    messages.reset()


def test_packaged_catalog_loads():
    assert "error.missing_credentials" in messages.catalog()
    assert messages.text("value.type_mismatch", name="x", actual="A", expected="TXT").endswith("expected TXT")


def test_override_from_mapping(gd):
    messages.use({"value.empty_name": "isim bos olamaz"})
    with pytest.raises(ValueError, match="isim bos olamaz"):
        gd.dns.get("example.com", "A", " ")


def test_override_from_file(tmp_path):
    path = tmp_path / "az.json"
    path.write_text(json.dumps({"value.empty_domain": "domen bos ola bilmez"}), encoding="utf-8")
    messages.use(path)
    assert messages.text("value.empty_domain") == "domen bos ola bilmez"


def test_unknown_keys_rejected():
    with pytest.raises(KeyError):
        messages.use({"nope": "x"})


