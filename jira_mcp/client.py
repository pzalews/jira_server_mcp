from __future__ import annotations
import logging
from typing import Any, Optional
import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from jira_mcp.config import Settings
from jira_mcp.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    JiraApiError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from jira_mcp.logging_config import host_only

logger = logging.getLogger("jira_mcp.client")

_RETRY_STATUS = {500, 502, 503, 504}


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, httpx.NetworkError):
        return True
    if isinstance(exc, JiraApiError) and exc.status_code in _RETRY_STATUS:
        return True
    return False


class JiraClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.jira_url
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **settings.auth_headers,
                **settings.custom_headers_dict,
            },
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "JiraClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    @staticmethod
    def _parse_errors(data: dict) -> str:
        msgs: list[str] = list(data.get("errorMessages", []))
        for field, msg in data.get("errors", {}).items():
            msgs.append(f"{field}: {msg}")
        return "; ".join(msgs) if msgs else str(data)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        code = response.status_code
        if code < 400:
            return
        try:
            data = response.json()
        except Exception:
            data = {}
        message = JiraClient._parse_errors(data) if data else response.text
        errors = data.get("errors", {}) if data else {}
        if code == 400:
            raise ValidationError(message)
        if code == 401:
            raise AuthenticationError(message or "Authentication required")
        if code == 403:
            raise AuthorizationError(message or "Permission denied")
        if code == 404:
            raise NotFoundError(message or "Resource not found")
        if code == 409:
            raise ConflictError(message or "Conflict")
        if code == 429:
            raise RateLimitError(message or "Rate limit exceeded")
        raise JiraApiError(message, status_code=code, errors=errors)

    @retry(
        retry=retry_if_exception(_should_retry),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        logger.debug("GET %s host=%s", path, host_only(self._base_url))
        response = await self._http.get(path, params=params)
        self._raise_for_status(response)
        return response.json()

    async def post(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> Any:
        logger.debug("POST %s host=%s", path, host_only(self._base_url))
        if files:
            # Multipart: add Atlassian CSRF bypass header required for attachments.
            # Do NOT set Content-Type — httpx sets it with multipart boundary automatically.
            headers = {"X-Atlassian-Token": "no-check"}
            response = await self._http.post(
                path,
                files=files,
                headers=headers,
            )
        else:
            response = await self._http.post(path, json=json)
        self._raise_for_status(response)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except Exception:
            return None

    async def put(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        logger.debug("PUT %s host=%s", path, host_only(self._base_url))
        response = await self._http.put(path, json=json)
        self._raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception:
            return None

    async def delete(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        logger.debug("DELETE %s host=%s", path, host_only(self._base_url))
        response = await self._http.delete(path, params=params)
        self._raise_for_status(response)

    async def paginate(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = 50,
        result_key: str = "values",
    ) -> list[Any]:
        params = dict(params or {})
        params["maxResults"] = page_size
        params["startAt"] = 0
        results: list[Any] = []
        while True:
            data = await self.get(path, params=params)
            if isinstance(data, dict):
                items = data.get(result_key, [])
                results.extend(items)
                total = data.get("total", len(results))
                start = data.get("startAt", 0)
                max_r = data.get("maxResults", page_size)
                if start + max_r >= total:
                    break
                params["startAt"] = start + max_r
            else:
                results.extend(data if isinstance(data, list) else [])
                break
        return results
