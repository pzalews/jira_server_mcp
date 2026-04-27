from __future__ import annotations
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.errors import ReadOnlyModeError


def register_comments(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def list_comments(
        issue_key: str,
        start_at: int = 0,
        max_results: int = 50,
        order_by: str = "created",
    ) -> dict:
        """List comments on a Jira issue."""
        return await client.get(
            f"/rest/api/2/issue/{issue_key}/comment",
            params={
                "startAt": start_at,
                "maxResults": min(max_results, 100),
                "orderBy": order_by,
            },
        )

    @mcp.tool
    async def add_comment(
        issue_key: str,
        body: str,
        visibility_type: Optional[str] = None,
        visibility_value: Optional[str] = None,
    ) -> dict:
        """Add a comment to a Jira issue.

        Args:
            issue_key: Target issue key.
            body: Comment text.
            visibility_type: Restrict visibility: 'role' or 'group'.
            visibility_value: Role/group name for visibility restriction.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "add_comment is disabled: server is in read-only mode"
            )
        payload: dict[str, Any] = {"body": body}
        if visibility_type and visibility_value:
            payload["visibility"] = {
                "type": visibility_type,
                "value": visibility_value,
            }
        return await client.post(
            f"/rest/api/2/issue/{issue_key}/comment", json=payload
        )

    @mcp.tool
    async def update_comment(
        issue_key: str,
        comment_id: str,
        body: str,
        visibility_type: Optional[str] = None,
        visibility_value: Optional[str] = None,
    ) -> dict:
        """Update the text of an existing comment on a Jira issue."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "update_comment is disabled: server is in read-only mode"
            )
        payload: dict[str, Any] = {"body": body}
        if visibility_type and visibility_value:
            payload["visibility"] = {
                "type": visibility_type,
                "value": visibility_value,
            }
        return await client.put(
            f"/rest/api/2/issue/{issue_key}/comment/{comment_id}", json=payload
        )

    @mcp.tool
    async def delete_comment(issue_key: str, comment_id: str) -> dict:
        """Delete a comment from a Jira issue. Returns structured confirmation."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "delete_comment is disabled: server is in read-only mode"
            )
        await client.delete(
            f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        )
        return {
            "deleted": True,
            "issue_key": issue_key,
            "comment_id": comment_id,
        }
