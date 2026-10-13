from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from goodconf import Field, GoodConf, GoodConfConfigDict
from pydantic import BaseModel, SecretStr

from ._version import __version__
from .errors import AuthenticationError
from .messages import text


class Endpoints(BaseModel):
    domains: str = "/{version}/domains"
    domain: str = "/{version}/domains/{domain}"
    available: str = "/{version}/domains/available"
    suggest: str = "/{version}/domains/suggest"
    tlds: str = "/{version}/domains/tlds"
    records: str = "/{version}/domains/{domain}/records"
    records_by_type: str = "/{version}/domains/{domain}/records/{type}"
    record: str = "/{version}/domains/{domain}/records/{type}/{name}"


class Settings(GoodConf):
    model_config = GoodConfConfigDict(
        env_prefix="GODADDY_",
        file_env_var="GODADDY_CONFIG",
        default_files=["godaddy.toml", "godaddy.yaml", "godaddy.yml", "godaddy.json"],
        extra="ignore",
        env_nested_delimiter="__",
    )

    api_key: SecretStr = Field(default=SecretStr(""), description=text("settings.api_key"))
    api_secret: SecretStr = Field(default=SecretStr(""), description=text("settings.api_secret"))
    environment: str = Field(default="production", description=text("settings.environment"))
    base_url: Optional[str] = Field(default=None, description=text("settings.base_url"))
    production_url: str = Field(default="https://api.godaddy.com", description=text("settings.production_url"))
    ote_url: str = Field(default="https://api.ote-godaddy.com", description=text("settings.ote_url"))
    api_version: str = Field(default="v1", description=text("settings.api_version"))
    endpoints: Endpoints = Field(default_factory=Endpoints, description=text("settings.endpoints"))
    shopper_id: Optional[str] = Field(default=None, description=text("settings.shopper_id"))
    timeout: float = Field(default=30.0, gt=0, description=text("settings.timeout"))
    max_retries: int = Field(default=3, ge=0, description=text("settings.max_retries"))
    max_retry_wait: float = Field(default=60.0, ge=0, description=text("settings.max_retry_wait"))
    backoff_base: float = Field(default=0.5, ge=0, description=text("settings.backoff_base"))
    backoff_cap: float = Field(default=8.0, ge=0, description=text("settings.backoff_cap"))
    page_size: int = Field(default=100, ge=1, le=1000, description=text("settings.page_size"))
    user_agent: str = Field(default="godaddy-python-sdk/{version}", description=text("settings.user_agent"))

    @property
    def environments(self) -> dict[str, str]:
        return {
            "production": self.production_url,
            "prod": self.production_url,
            "ote": self.ote_url,
            "test": self.ote_url,
        }

    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        env = self.environment.strip().lower()
        if env not in self.environments:
            choices = ", ".join(sorted({"production", "ote"}))
            raise ValueError(text("error.unknown_environment", environment=env, choices=choices))
        return self.environments[env].rstrip("/")

    def path(self, endpoint: str, **params: str) -> str:
        template = getattr(self.endpoints, endpoint)
        values = {key: quote(str(value), safe="@") for key, value in params.items()}
        return template.format(version=quote(self.api_version, safe=""), **values)

    def resolved_user_agent(self) -> str:
        return self.user_agent.replace("{version}", __version__)

    def require_credentials(self) -> tuple[str, str]:
        key = self.api_key.get_secret_value()
        secret = self.api_secret.get_secret_value()
        if not key or not secret:
            raise AuthenticationError(text("error.missing_credentials"))
        return key, secret


Settings.__doc__ = text("settings.description")


def load_settings(config_file: Optional[str] = None, **overrides: Any) -> Settings:
    given = {key: value for key, value in overrides.items() if value is not None}
    return Settings(load=True, config_file=config_file, **given)
