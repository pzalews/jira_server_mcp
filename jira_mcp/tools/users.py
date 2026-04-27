from __future__ import annotations
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.errors import ValidationError


def register_users(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def search_users(
        query: str,
        max_results: int = 50,
        include_inactive: bool = False,
    ) -> list[dict]:
        """Search for Jira users by display name, email, or username.

        Args:
            query: Search string (partial name, email, or username).
            max_results: Maximum results to return (1-200).
            include_inactive: If True, include inactive/deactivated users.
        """
        params: dict[str, Any] = {
            "query": query,
            "maxResults": min(max_results, 200),
            "includeInactive": str(include_inactive).lower(),
        }
        result = await client.get("/rest/api/2/user/search", params=params)
        return result if isinstance(result, list) else []

    @mcp.tool
    async def get_user(
        account_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> dict:
        """Get a Jira user profile by account ID or username.

        Provide either account_id or username (not both).
        """
        if not account_id and not username:
            raise ValidationError("Provide either account_id or username")
        params: dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        elif username:
            params["username"] = username
        return await client.get("/rest/api/2/user", params=params)

    @mcp.tool
    async def validate_jql(jql: str) -> dict:
        """Validate a JQL query string and return parsing errors if any."""
        return await client.post(
            "/rest/api/2/jql/parse",
            json={"queries": [jql]},
        )

    @mcp.tool
    async def search_by_jql(
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: str = "summary,status,assignee,priority,issuetype,created,updated",
    ) -> dict:
        """Execute a JQL query and return structured issue results.

        Returns issues with summary, status, assignee, priority, type, dates.
        Use fields='*all' for all fields or specify a comma-separated list.
        """
        params: dict[str, Any] = {
            "jql": jql,
            "maxResults": max(1, min(max_results, 200)),
            "startAt": max(0, start_at),
            "fields": fields,
        }
        return await client.get("/rest/api/2/search", params=params)
