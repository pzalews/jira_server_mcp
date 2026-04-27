from __future__ import annotations
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings


def register_projects(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def get_server_info() -> dict:
        """Get Jira server version and build information."""
        return await client.get("/rest/api/2/serverInfo")

    @mcp.tool
    async def get_myself() -> dict:
        """Get the profile of the currently authenticated user."""
        return await client.get("/rest/api/2/myself")

    @mcp.tool
    async def list_projects(
        project_type: Optional[str] = None,
        expand: Optional[str] = None,
    ) -> list[dict]:
        """List all projects accessible to the current user.

        Args:
            project_type: Filter by type: 'software', 'service_desk', 'business'.
            expand: Comma-separated fields to expand (e.g., 'description,lead').
        """
        params: dict[str, Any] = {}
        if project_type:
            params["type"] = project_type
        if expand:
            params["expand"] = expand
        result = await client.get("/rest/api/2/project", params=params)
        return result if isinstance(result, list) else []

    @mcp.tool
    async def get_project(project_key: str) -> dict:
        """Get full details for a project by its key (e.g., 'PROJ')."""
        return await client.get(f"/rest/api/2/project/{project_key.upper()}")

    @mcp.tool
    async def get_project_versions(project_key: str) -> list[dict]:
        """List all fix versions defined for a project."""
        result = await client.get(f"/rest/api/2/project/{project_key.upper()}/versions")
        return result if isinstance(result, list) else []

    @mcp.tool
    async def get_project_components(project_key: str) -> list[dict]:
        """List all components defined for a project."""
        result = await client.get(
            f"/rest/api/2/project/{project_key.upper()}/components"
        )
        return result if isinstance(result, list) else []
