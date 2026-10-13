from __future__ import annotations

from typing import Any

from ._base import AsyncClient, SyncClient
from .resources import DNS, AsyncDNS, AsyncDomains, Domains


class GoDaddy(SyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = Domains(self)
        self.dns = DNS(self)


class AsyncGoDaddy(AsyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = AsyncDomains(self)
        self.dns = AsyncDNS(self)
