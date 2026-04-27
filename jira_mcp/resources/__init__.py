from __future__ import annotations
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings


def register_resources(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.resource("jira://config/effective")
    def get_effective_config() -> dict:
        """Current server configuration with all secrets redacted."""
        return settings.redacted_dict

    @mcp.resource("jira://myself")
    async def get_myself_resource() -> dict:
        """Profile of the currently authenticated Jira user."""
        return await client.get("/rest/api/2/myself")

    @mcp.resource("jira://projects")
    async def get_projects_resource() -> list:
        """All Jira projects accessible to the current user."""
        result = await client.get("/rest/api/2/project")
        return result if isinstance(result, list) else []

    @mcp.resource("jira://issue/{issue_key}")
    async def get_issue_resource(issue_key: str) -> dict:
        """Full issue details for a given issue key."""
        return await client.get(f"/rest/api/2/issue/{issue_key}")

    @mcp.resource("jira://project/{project_key}")
    async def get_project_resource(project_key: str) -> dict:
        """Full project details for a given project key."""
        return await client.get(f"/rest/api/2/project/{project_key}")
