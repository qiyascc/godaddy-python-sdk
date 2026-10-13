from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .messages import text


@dataclass(frozen=True)
class FieldError:
    path: str
    code: str
    message: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> FieldError:
        return cls(
            path=str(data.get("path", "")),
            code=str(data.get("code", "")),
            message=str(data.get("message", "")),
        )


class GoDaddyError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        fields: Optional[list[FieldError]] = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.fields = fields or []
        self.response = response

    def __str__(self) -> str:
        parts = []
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        if self.code:
            parts.append(self.code)
        parts.append(self.message)
        text = " ".join(parts)
        if self.fields:
            details = "; ".join(f"{f.path}: {f.message}" for f in self.fields)
            text = f"{text} ({details})"
        return text


class APIConnectionError(GoDaddyError):
    pass


class APITimeoutError(APIConnectionError):
    pass


class APIStatusError(GoDaddyError):
    pass


class ValidationError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ConflictError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIStatusError):
    pass


_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def retry_after_from(response: httpx.Response, body: Any = None) -> Optional[float]:
    if isinstance(body, dict):
        value = body.get("retryAfterSec")
        if isinstance(value, (int, float)):
            return float(value)
    header = response.headers.get("Retry-After")
    if header:
        try:
            return float(header)
        except ValueError:
            return None
    return None


def error_from_response(response: httpx.Response) -> APIStatusError:
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        message = str(body.get("message") or response.reason_phrase or text("error.request_failed"))
        code = body.get("code")
        fields = [FieldError.from_api(f) for f in body.get("fields") or [] if isinstance(f, dict)]
    else:
        message = response.text.strip() or response.reason_phrase or text("error.request_failed")
        code = None
        fields = []

    status = response.status_code
    kwargs: dict[str, Any] = dict(status_code=status, code=code, fields=fields, response=response)

    if status == 429:
        return RateLimitError(message, retry_after=retry_after_from(response, body), **kwargs)
    if status >= 500:
        return ServerError(message, **kwargs)
    return _STATUS_MAP.get(status, APIStatusError)(message, **kwargs)
