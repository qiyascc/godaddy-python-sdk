from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Union

from .messages import text


class RecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"
    CAA = "CAA"

    def __str__(self) -> str:
        return self.value


RecordTypeLike = Union[RecordType, str]


def record_type(value: RecordTypeLike) -> str:
    kind = value.value if isinstance(value, RecordType) else str(value).strip().upper()
    if not kind:
        raise ValueError(text("value.empty_type"))
    return kind


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    stamp = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


@dataclass
class DNSRecord:
    type: str
    name: str
    data: str
    ttl: int = 600
    priority: Optional[int] = None
    weight: Optional[int] = None
    port: Optional[int] = None
    service: Optional[str] = None
    protocol: Optional[str] = None

    def __post_init__(self) -> None:
        self.type = record_type(self.type)

    @classmethod
    def a(cls, name: str, ip: str, ttl: int = 600) -> DNSRecord:
        return cls("A", name, str(ipaddress.IPv4Address(ip)), ttl)

    @classmethod
    def aaaa(cls, name: str, ip: str, ttl: int = 600) -> DNSRecord:
        return cls("AAAA", name, str(ipaddress.IPv6Address(ip)), ttl)

    @classmethod
    def cname(cls, name: str, target: str, ttl: int = 3600) -> DNSRecord:
        return cls("CNAME", name, target, ttl)

    @classmethod
    def txt(cls, name: str, value: str, ttl: int = 600) -> DNSRecord:
        return cls("TXT", name, value, ttl)

    @classmethod
    def mx(cls, name: str, host: str, priority: int = 10, ttl: int = 3600) -> DNSRecord:
        return cls("MX", name, host, ttl, priority=priority)

    @classmethod
    def srv(
        cls,
        service: str,
        protocol: str,
        name: str,
        target: str,
        port: int,
        priority: int = 0,
        weight: int = 0,
        ttl: int = 3600,
    ) -> DNSRecord:
        return cls(
            "SRV", name, target, ttl,
            priority=priority, weight=weight, port=port, service=service, protocol=protocol,
        )

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DNSRecord:
        return cls(
            type=data.get("type", ""),
            name=data.get("name", ""),
            data=data.get("data", ""),
            ttl=int(data.get("ttl", 600)),
            priority=data.get("priority"),
            weight=data.get("weight"),
            port=data.get("port"),
            service=data.get("service"),
            protocol=data.get("protocol"),
        )

    def to_api(self, include_identity: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {"data": self.data, "ttl": self.ttl}
        if include_identity:
            payload = {"type": self.type, "name": self.name, **payload}
        for key in ("priority", "weight", "port", "service", "protocol"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return payload


@dataclass
class Contact:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    organization: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: Optional[dict[str, Any]]) -> Optional[Contact]:
        if not data:
            return None
        return cls(
            first_name=data.get("nameFirst", ""),
            last_name=data.get("nameLast", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            organization=data.get("organization", ""),
            raw=data,
        )


@dataclass
class Domain:
    domain: str
    domain_id: Optional[int] = None
    status: str = ""
    created_at: Optional[datetime] = None
    expires: Optional[datetime] = None
    renew_auto: bool = False
    renewable: bool = False
    locked: bool = False
    privacy: bool = False
    expiration_protected: bool = False
    transfer_protected: bool = False
    name_servers: list[str] = field(default_factory=list)
    registrant: Optional[Contact] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Domain:
        contacts = data.get("contactRegistrant")
        return cls(
            domain=data.get("domain", ""),
            domain_id=data.get("domainId"),
            status=data.get("status", ""),
            created_at=_parse_datetime(data.get("createdAt")),
            expires=_parse_datetime(data.get("expires")),
            renew_auto=bool(data.get("renewAuto", False)),
            renewable=bool(data.get("renewable", False)),
            locked=bool(data.get("locked", False)),
            privacy=bool(data.get("privacy", False)),
            expiration_protected=bool(data.get("expirationProtected", False)),
            transfer_protected=bool(data.get("transferProtected", False)),
            name_servers=list(data.get("nameServers") or []),
            registrant=Contact.from_api(contacts),
            raw=data,
        )


@dataclass
class Availability:
    domain: str
    available: bool
    definitive: bool = False
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    period: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Availability:
        micros = data.get("price")
        price = (Decimal(micros) / Decimal(1_000_000)) if micros is not None else None
        return cls(
            domain=data.get("domain", ""),
            available=bool(data.get("available", False)),
            definitive=bool(data.get("definitive", False)),
            price=price,
            currency=data.get("currency"),
            period=data.get("period"),
            raw=data,
        )


@dataclass
class Suggestion:
    domain: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Suggestion:
        return cls(domain=data.get("domain", ""))


@dataclass
class Tld:
    name: str
    type: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Tld:
        return cls(name=data.get("name", ""), type=data.get("type", ""))
