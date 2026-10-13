from __future__ import annotations

import json
from typing import Any, Callable

import httpx
import pytest

from godaddy import AsyncGoDaddy, GoDaddy

Handler = Callable[[httpx.Request], httpx.Response]


class Recorder:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.responses: list[httpx.Response] = []

    def queue(self, status: int = 200, body: Any = None, headers: dict[str, str] | None = None) -> None:
        content = b"" if body is None else json.dumps(body).encode()
        self.responses.append(httpx.Response(status, content=content, headers=headers or {}))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if not self.responses:
            return httpx.Response(200, content=b"[]")
        return self.responses.pop(0)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def body(self, index: int = -1) -> Any:
        return json.loads(self.requests[index].content)


@pytest.fixture
def api() -> Recorder:
    return Recorder()


@pytest.fixture
def gd(api: Recorder) -> GoDaddy:
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = GoDaddy("key", "secret", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


@pytest.fixture
def agd(api: Recorder) -> AsyncGoDaddy:
    http = httpx.AsyncClient(transport=httpx.MockTransport(api))
    client = AsyncGoDaddy("key", "secret", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client
