from __future__ import annotations


class JiraMcpError(Exception):
    """Base class for all Jira MCP errors."""


class ConfigurationError(JiraMcpError):
    """Invalid or missing configuration."""


class AuthenticationError(JiraMcpError):
    """Authentication failed (HTTP 401)."""


class AuthorizationError(JiraMcpError):
    """Insufficient permissions (HTTP 403)."""


class NotFoundError(JiraMcpError):
    """Resource not found (HTTP 404)."""


class ConflictError(JiraMcpError):
    """Conflict with current state (HTTP 409)."""


class ValidationError(JiraMcpError):
    """Input validation failed (HTTP 400)."""


class RateLimitError(JiraMcpError):
    """Rate limit exceeded (HTTP 429)."""


class ReadOnlyModeError(JiraMcpError):
    """Operation blocked because JIRA_READ_ONLY=true."""


class JiraApiError(JiraMcpError):
    """Unmapped Jira API error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        errors: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or {}


class JiraSoftwareUnavailableError(JiraMcpError):
    """Jira Software (Agile) APIs not available on this instance."""
