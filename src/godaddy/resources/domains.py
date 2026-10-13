from __future__ import annotations

from typing import Any, AsyncIterator, Iterable, Iterator, Optional

from .._base import Call
from ..messages import text
from ..models import Availability, Domain, Suggestion, Tld
from .dns import _domain


def _domains(payload: Any) -> list[Domain]:
    return [Domain.from_api(item) for item in payload or [] if isinstance(item, dict)]


def _bulk_availability(payload: Any) -> list[Availability]:
    if not isinstance(payload, dict):
        return []
    return [Availability.from_api(item) for item in payload.get("domains") or []]


class _DomainsBase:
    def __init__(self, client: Any) -> None:
        self._client = client
        self.page_size = client.settings.page_size

    def _run(self, call: Call) -> Any:
        return self._client._execute(call)

    def _list_call(
        self,
        statuses: Optional[Iterable[str]],
        status_groups: Optional[Iterable[str]],
        limit: Optional[int],
        marker: Optional[str],
        includes: Optional[Iterable[str]],
    ) -> Call:
        params = {
            "statuses": list(statuses) if statuses else None,
            "statusGroups": list(status_groups) if status_groups else None,
            "limit": limit,
            "marker": marker,
            "includes": list(includes) if includes else None,
        }
        return Call("GET", "/v1/domains", params=params, parse=_domains)

    def list(
        self,
        *,
        statuses: Optional[Iterable[str]] = None,
        status_groups: Optional[Iterable[str]] = None,
        limit: Optional[int] = None,
        marker: Optional[str] = None,
        includes: Optional[Iterable[str]] = None,
    ) -> Any:
        return self._run(self._list_call(statuses, status_groups, limit, marker, includes))

    def get(self, domain: str) -> Any:
        return self._run(Call("GET", f"/v1/domains/{_domain(domain)}", parse=Domain.from_api))

    def available(self, domain: str, *, full_check: bool = False, for_transfer: bool = False) -> Any:
        params = {
            "domain": domain.strip().lower(),
            "checkType": "FULL" if full_check else "FAST",
            "forTransfer": for_transfer,
        }
        return self._run(Call("GET", "/v1/domains/available", params=params, parse=Availability.from_api))

    def available_many(self, domains: Iterable[str], *, full_check: bool = False) -> Any:
        body = [d.strip().lower() for d in domains]
        if not body:
            raise ValueError(text("value.no_domains"))
        params = {"checkType": "FULL" if full_check else "FAST"}
        return self._run(Call("POST", "/v1/domains/available", params=params, json=body, parse=_bulk_availability))

    def suggest(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        tlds: Optional[Iterable[str]] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        length_min: Optional[int] = None,
        length_max: Optional[int] = None,
        wait_ms: Optional[int] = None,
    ) -> Any:
        params = {
            "query": query,
            "limit": limit,
            "tlds": list(tlds) if tlds else None,
            "country": country,
            "city": city,
            "lengthMin": length_min,
            "lengthMax": length_max,
            "waitMs": wait_ms,
        }
        parse = lambda payload: [Suggestion.from_api(item) for item in payload or []]
        return self._run(Call("GET", "/v1/domains/suggest", params=params, parse=parse))

    def tlds(self) -> Any:
        parse = lambda payload: [Tld.from_api(item) for item in payload or []]
        return self._run(Call("GET", "/v1/domains/tlds", parse=parse))

    def update(
        self,
        domain: str,
        *,
        locked: Optional[bool] = None,
        renew_auto: Optional[bool] = None,
        name_servers: Optional[Iterable[str]] = None,
        subaccount_id: Optional[str] = None,
    ) -> Any:
        body: dict[str, Any] = {}
        if locked is not None:
            body["locked"] = locked
        if renew_auto is not None:
            body["renewAuto"] = renew_auto
        if name_servers is not None:
            body["nameServers"] = list(name_servers)
        if subaccount_id is not None:
            body["subaccountId"] = subaccount_id
        if not body:
            raise ValueError(text("value.update_needs_fields"))
        return self._run(Call("PATCH", f"/v1/domains/{_domain(domain)}", json=body, parse=lambda _: None))


class Domains(_DomainsBase):
    def iter(
        self,
        *,
        statuses: Optional[Iterable[str]] = None,
        status_groups: Optional[Iterable[str]] = None,
        includes: Optional[Iterable[str]] = None,
    ) -> Iterator[Domain]:
        marker = None
        while True:
            page = self._run(self._list_call(statuses, status_groups, self.page_size, marker, includes))
            yield from page
            if len(page) < self.page_size:
                return
            marker = page[-1].domain


class AsyncDomains(_DomainsBase):
    async def iter(
        self,
        *,
        statuses: Optional[Iterable[str]] = None,
        status_groups: Optional[Iterable[str]] = None,
        includes: Optional[Iterable[str]] = None,
    ) -> AsyncIterator[Domain]:
        marker = None
        while True:
            page = await self._run(self._list_call(statuses, status_groups, self.page_size, marker, includes))
            for item in page:
                yield item
            if len(page) < self.page_size:
                return
            marker = page[-1].domain
