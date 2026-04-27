from __future__ import annotations
import json
import logging
import sys
from typing import Any, Optional
from urllib.parse import urlparse


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            data.update(record.extra)  # type: ignore[arg-type]
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


def setup_logging(log_path: Optional[str] = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_path:
        handlers.append(logging.FileHandler(log_path))
    formatter = _JsonFormatter()
    logger = logging.getLogger("jira_mcp")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    for h in handlers:
        h.setFormatter(formatter)
        logger.addHandler(h)
    logger.propagate = False


def host_only(url: str) -> str:
    """Return only the hostname to avoid leaking tokens in URLs."""
    try:
        return urlparse(url).hostname or "<unknown>"
    except Exception:
        return "<unknown>"


def log_tool_call(
    logger: logging.Logger,
    *,
    tool: str,
    jira_url: str,
    duration_ms: float,
    status: str,
    issue_key: Optional[str] = None,
    project_key: Optional[str] = None,
    error_category: Optional[str] = None,
) -> None:
    extra: dict[str, Any] = {
        "tool": tool,
        "jira_host": host_only(jira_url),
        "duration_ms": round(duration_ms, 2),
        "status": status,
    }
    if issue_key:
        extra["issue_key"] = issue_key
    if project_key:
        extra["project_key"] = project_key
    if error_category:
        extra["error_category"] = error_category
    logger.info("tool_call", extra={"extra": extra})
