from __future__ import annotations
import base64
from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _unquote(v: str) -> str:
    """Strip surrounding quotes that Docker Compose passes through literally."""
    return v.strip().strip('"').strip("'")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jira_url: str
    jira_token: Optional[str] = None
    jira_username: Optional[str] = None
    jira_password: Optional[str] = None
    jira_default_project: Optional[str] = None
    jira_read_only: bool = False
    jira_log_path: Optional[str] = None
    jira_custom_headers: Optional[str] = None
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    @field_validator("jira_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        v = _unquote(v).rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"JIRA_URL must start with 'http://' or 'https://', got: {v!r}"
            )
        return v

    @field_validator("jira_token", "jira_username", "jira_password", mode="before")
    @classmethod
    def unquote_credentials(cls, v: Optional[str]) -> Optional[str]:
        return _unquote(v) if v is not None else v

    @property
    def auth_headers(self) -> dict[str, str]:
        if self.jira_token:
            return {"Authorization": f"Bearer {self.jira_token}"}
        if self.jira_username and self.jira_password:
            creds = base64.b64encode(
                f"{self.jira_username}:{self.jira_password}".encode()
            ).decode()
            return {"Authorization": f"Basic {creds}"}
        return {}

    @property
    def custom_headers_dict(self) -> dict[str, str]:
        if not self.jira_custom_headers:
            return {}
        result: dict[str, str] = {}
        for pair in self.jira_custom_headers.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, _, v = pair.partition("=")
                result[k.strip()] = v.strip()
        return result

    @property
    def redacted_dict(self) -> dict:
        return {
            "jira_url": self.jira_url,
            "jira_token": "***" if self.jira_token else None,
            "jira_username": self.jira_username,
            "jira_password": "***" if self.jira_password else None,
            "jira_default_project": self.jira_default_project,
            "jira_read_only": self.jira_read_only,
            "jira_log_path": self.jira_log_path,
            "jira_custom_headers": "***" if self.jira_custom_headers else None,
            "mcp_transport": self.mcp_transport,
            "mcp_host": self.mcp_host,
            "mcp_port": self.mcp_port,
        }
