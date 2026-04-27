from __future__ import annotations
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings


def register_workflows(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def list_issue_types() -> list[dict]:
        """List all issue types available on this Jira instance."""
        result = await client.get("/rest/api/2/issuetype")
        return result if isinstance(result, list) else []

    @mcp.tool
    async def list_fields() -> list[dict]:
        """List all Jira fields (system and custom) with their IDs and schemas."""
        result = await client.get("/rest/api/2/field")
        return result if isinstance(result, list) else []

    @mcp.tool
    async def get_create_metadata(
        project_keys: Optional[str] = None,
        issue_type_names: Optional[str] = None,
        expand: str = "projects.issuetypes.fields",
    ) -> dict:
        """Get issue creation metadata: required fields, allowed values per project/type.

        Args:
            project_keys: Comma-separated project keys to filter by.
            issue_type_names: Comma-separated issue type names to filter by.
            expand: Expansion level (default returns full field schemas).
        """
        params: dict[str, Any] = {"expand": expand}
        if project_keys:
            params["projectKeys"] = project_keys
        if issue_type_names:
            params["issuetypeNames"] = issue_type_names
        return await client.get("/rest/api/2/issue/createmeta", params=params)

    @mcp.tool
    async def get_edit_metadata(issue_key: str) -> dict:
        """Get the editable fields and their constraints for an existing issue."""
        return await client.get(f"/rest/api/2/issue/{issue_key}/editmeta")

    @mcp.tool
    async def get_transition_metadata(issue_key: str) -> dict:
        """Get transitions with their required fields for an issue (expanded view)."""
        return await client.get(
            f"/rest/api/2/issue/{issue_key}/transitions",
            params={"expand": "transitions.fields"},
        )
