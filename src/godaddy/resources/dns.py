from __future__ import annotations

import ipaddress
from typing import Any, Iterable, Optional, Sequence, Union
from urllib.parse import quote

from .._base import Call
from ..messages import text
from ..models import DNSRecord, RecordType, RecordTypeLike, record_type

RecordValues = Union[str, DNSRecord, Iterable[Union[str, DNSRecord]]]


def _domain(domain: str) -> str:
    value = domain.strip().lower().rstrip(".")
    if not value:
        raise ValueError(text("value.empty_domain"))
    return quote(value, safe="")


def _name(name: str) -> str:
    value = name.strip()
    if not value:
        raise ValueError(text("value.empty_name"))
    return quote(value, safe="@")


def _records(payload: Any) -> list[DNSRecord]:
    return [DNSRecord.from_api(item) for item in payload or [] if isinstance(item, dict)]


def _record_bodies(values: RecordValues, ttl: int, include_identity: bool = False) -> list[dict[str, Any]]:
    if isinstance(values, (str, DNSRecord)):
        values = [values]
    bodies = []
    for value in values:
        if isinstance(value, DNSRecord):
            bodies.append(value.to_api(include_identity=include_identity))
        else:
            bodies.append({"data": str(value), "ttl": ttl})
    if not bodies:
        raise ValueError(text("value.no_values"))
    return bodies


def ip_record_type(ip: str) -> RecordType:
    version = ipaddress.ip_address(ip).version
    return RecordType.A if version == 4 else RecordType.AAAA


class DNS:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _run(self, call: Call) -> Any:
        return self._client._execute(call)

    def list(
        self,
        domain: str,
        type: Optional[RecordTypeLike] = None,
        name: Optional[str] = None,
        *,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Any:
        path = f"/v1/domains/{_domain(domain)}/records"
        wanted_name = name.strip() if name else None

        if type is not None:
            path += f"/{quote(record_type(type), safe='')}"
            if wanted_name:
                path += f"/{_name(wanted_name)}"
            parse = _records
        else:
            def parse(payload: Any) -> list[DNSRecord]:
                records = _records(payload)
                if wanted_name:
                    records = [r for r in records if r.name == wanted_name]
                return records

        return self._run(Call("GET", path, params={"offset": offset, "limit": limit}, parse=parse))

    def get(self, domain: str, type: RecordTypeLike, name: str) -> Any:
        path = f"/v1/domains/{_domain(domain)}/records/{quote(record_type(type), safe='')}/{_name(name)}"
        return self._run(Call("GET", path, parse=_records))

    def exists(self, domain: str, type: RecordTypeLike, name: str) -> Any:
        path = f"/v1/domains/{_domain(domain)}/records/{quote(record_type(type), safe='')}/{_name(name)}"
        return self._run(Call("GET", path, parse=lambda payload: bool(_records(payload))))

    def add(self, domain: str, *records: DNSRecord) -> Any:
        if not records:
            raise ValueError(text("value.add_needs_records"))
        body = [record.to_api() for record in records]
        return self._run(Call("PATCH", f"/v1/domains/{_domain(domain)}/records", json=body, parse=lambda _: None))

    def replace(
        self,
        domain: str,
        type: RecordTypeLike,
        name: str,
        values: RecordValues,
        *,
        ttl: int = 600,
    ) -> Any:
        path = f"/v1/domains/{_domain(domain)}/records/{quote(record_type(type), safe='')}/{_name(name)}"
        body = _record_bodies(values, ttl)
        return self._run(Call("PUT", path, json=body, parse=lambda _: None))

    def replace_type(self, domain: str, type: RecordTypeLike, records: Sequence[DNSRecord]) -> Any:
        kind = record_type(type)
        for record in records:
            if record.type != kind:
                raise ValueError(text("value.type_mismatch", name=record.name, actual=record.type, expected=kind))
        body = [{"name": r.name, **r.to_api(include_identity=False)} for r in records]
        path = f"/v1/domains/{_domain(domain)}/records/{quote(kind, safe='')}"
        return self._run(Call("PUT", path, json=body, parse=lambda _: None))

    def replace_all(self, domain: str, records: Sequence[DNSRecord]) -> Any:
        body = [record.to_api() for record in records]
        return self._run(Call("PUT", f"/v1/domains/{_domain(domain)}/records", json=body, parse=lambda _: None))

    def delete(self, domain: str, type: RecordTypeLike, name: str, *, missing_ok: bool = False) -> Any:
        path = f"/v1/domains/{_domain(domain)}/records/{quote(record_type(type), safe='')}/{_name(name)}"
        allow = frozenset({404}) if missing_ok else frozenset()
        return self._run(Call("DELETE", path, parse=lambda _: None, allow_status=allow))

    def point(self, domain: str, name: str, ip: str, *, ttl: int = 600) -> Any:
        kind = ip_record_type(ip)
        return self.replace(domain, kind, name, [str(ipaddress.ip_address(ip))], ttl=ttl)

    def unpoint(self, domain: str, name: str, ip_version: int = 4) -> Any:
        kind = RecordType.A if ip_version == 4 else RecordType.AAAA
        return self.delete(domain, kind, name, missing_ok=True)

    def alias(self, domain: str, name: str, target: str, *, ttl: int = 3600) -> Any:
        return self.replace(domain, RecordType.CNAME, name, [target], ttl=ttl)

    def set_txt(self, domain: str, name: str, values: Union[str, Iterable[str]], *, ttl: int = 600) -> Any:
        return self.replace(domain, RecordType.TXT, name, values, ttl=ttl)


class AsyncDNS(DNS):
    pass
