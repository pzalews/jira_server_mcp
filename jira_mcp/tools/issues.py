from __future__ import annotations
import logging
import time
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.errors import ReadOnlyModeError, ValidationError
from jira_mcp.logging_config import log_tool_call

_logger = logging.getLogger("jira_mcp.tools.issues")


def register_issues(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def search_issues(
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: str = "",
    ) -> dict:
        """Search Jira issues using JQL. Returns paginated results.

        Args:
            jql: JQL query string (e.g., 'project=PROJ AND status=Open').
            max_results: Maximum issues to return (1-200).
            start_at: Pagination offset.
            fields: Comma-separated field names (empty = all fields).
        """
        params: dict[str, Any] = {
            "jql": jql,
            "maxResults": max(1, min(max_results, 200)),
            "startAt": max(0, start_at),
        }
        if fields:
            params["fields"] = fields
        t0 = time.monotonic()
        try:
            result = await client.get("/rest/api/2/search", params=params)
            log_tool_call(
                _logger,
                tool="search_issues",
                jira_url=client._base_url,
                duration_ms=(time.monotonic() - t0) * 1000,
                status="ok",
            )
            return result
        except Exception as exc:
            log_tool_call(
                _logger,
                tool="search_issues",
                jira_url=client._base_url,
                duration_ms=(time.monotonic() - t0) * 1000,
                status="error",
                error_category=type(exc).__name__,
            )
            raise

    @mcp.tool
    async def get_issue(
        issue_key: str,
        fields: str = "",
        expand: str = "",
    ) -> dict:
        """Get full details for a Jira issue by key (e.g., 'PROJ-123').

        Args:
            issue_key: Issue key in format PROJECT-NUMBER.
            fields: Comma-separated fields to return (empty = all).
            expand: Comma-separated expansions (e.g., 'changelog,renderedFields').
        """
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        if expand:
            params["expand"] = expand
        t0 = time.monotonic()
        try:
            result = await client.get(f"/rest/api/2/issue/{issue_key}", params=params)
            log_tool_call(
                _logger,
                tool="get_issue",
                jira_url=client._base_url,
                duration_ms=(time.monotonic() - t0) * 1000,
                status="ok",
                issue_key=issue_key,
            )
            return result
        except Exception as exc:
            log_tool_call(
                _logger,
                tool="get_issue",
                jira_url=client._base_url,
                duration_ms=(time.monotonic() - t0) * 1000,
                status="error",
                issue_key=issue_key,
                error_category=type(exc).__name__,
            )
            raise

    @mcp.tool
    async def create_issue(
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[list[str]] = None,
        components: Optional[list[str]] = None,
        fix_versions: Optional[list[str]] = None,
    ) -> dict:
        """Create a new Jira issue. Returns the created issue key and self URL.

        Args:
            project_key: Target project key (e.g., 'PROJ').
            summary: Issue title/summary.
            issue_type: Issue type name (e.g., 'Bug', 'Story', 'Task').
            description: Full description text.
            assignee: Username or account ID of the assignee.
            priority: Priority name (e.g., 'High', 'Medium', 'Low').
            labels: List of label strings.
            components: List of component names.
            fix_versions: List of fix version names.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "create_issue is disabled: server is in read-only mode (JIRA_READ_ONLY=true)"
            )
        issue_fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            issue_fields["description"] = description
        if assignee:
            issue_fields["assignee"] = {"name": assignee}
        if priority:
            issue_fields["priority"] = {"name": priority}
        if labels:
            issue_fields["labels"] = labels
        if components:
            issue_fields["components"] = [{"name": c} for c in components]
        if fix_versions:
            issue_fields["fixVersions"] = [{"name": v} for v in fix_versions]
        return await client.post("/rest/api/2/issue", json={"fields": issue_fields})

    @mcp.tool
    async def update_issue(
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[list[str]] = None,
        components: Optional[list[str]] = None,
        fix_versions: Optional[list[str]] = None,
    ) -> dict:
        """Update one or more fields on an existing Jira issue.

        Only provided fields are updated; omitted fields are unchanged.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "update_issue is disabled: server is in read-only mode"
            )
        issue_fields: dict[str, Any] = {}
        if summary is not None:
            issue_fields["summary"] = summary
        if description is not None:
            issue_fields["description"] = description
        if assignee is not None:
            issue_fields["assignee"] = {"name": assignee}
        if priority is not None:
            issue_fields["priority"] = {"name": priority}
        if labels is not None:
            issue_fields["labels"] = labels
        if components is not None:
            issue_fields["components"] = [{"name": c} for c in components]
        if fix_versions is not None:
            issue_fields["fixVersions"] = [{"name": v} for v in fix_versions]
        if not issue_fields:
            raise ValidationError("At least one field must be provided to update_issue")
        await client.put(f"/rest/api/2/issue/{issue_key}", json={"fields": issue_fields})
        return {"updated": True, "issue_key": issue_key}

    @mcp.tool
    async def delete_issue(issue_key: str, delete_subtasks: bool = False) -> dict:
        """Permanently delete a Jira issue (and optionally its subtasks).

        Returns structured confirmation. This action is irreversible.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "delete_issue is disabled: server is in read-only mode"
            )
        await client.delete(
            f"/rest/api/2/issue/{issue_key}",
            params={"deleteSubtasks": str(delete_subtasks).lower()},
        )
        return {"deleted": True, "issue_key": issue_key}

    @mcp.tool
    async def assign_issue(issue_key: str, assignee: Optional[str] = None) -> dict:
        """Assign a Jira issue to a user. Pass null/None to unassign.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123').
            assignee: Username or account ID. Omit or pass null to unassign.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "assign_issue is disabled: server is in read-only mode"
            )
        body: dict[str, Any] = {"name": assignee} if assignee else {"name": None}
        await client.put(f"/rest/api/2/issue/{issue_key}/assignee", json=body)
        return {"assigned": True, "issue_key": issue_key, "assignee": assignee}

    @mcp.tool
    async def link_issues(
        from_issue_key: str,
        to_issue_key: str,
        link_type: str,
        comment_body: Optional[str] = None,
    ) -> dict:
        """Create a link between two Jira issues.

        Args:
            from_issue_key: Source issue key.
            to_issue_key: Target issue key.
            link_type: Link type name (e.g., 'blocks', 'is blocked by', 'relates to').
            comment_body: Optional comment to add when creating the link.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "link_issues is disabled: server is in read-only mode"
            )
        body: dict[str, Any] = {
            "type": {"name": link_type},
            "inwardIssue": {"key": from_issue_key},
            "outwardIssue": {"key": to_issue_key},
        }
        if comment_body:
            body["comment"] = {"body": comment_body}
        await client.post("/rest/api/2/issueLink", json=body)
        return {
            "linked": True,
            "from": from_issue_key,
            "to": to_issue_key,
            "link_type": link_type,
        }

    @mcp.tool
    async def get_issue_transitions(issue_key: str) -> dict:
        """List all available workflow transitions for an issue in its current state."""
        return await client.get(f"/rest/api/2/issue/{issue_key}/transitions")

    @mcp.tool
    async def transition_issue(
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> dict:
        """Execute a workflow transition on a Jira issue.

        Args:
            issue_key: Issue to transition.
            transition_id: ID from get_issue_transitions (e.g., '31').
            comment: Optional comment to add during transition.
            resolution: Optional resolution name when closing (e.g., 'Fixed', 'Won\\'t Fix').
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "transition_issue is disabled: server is in read-only mode"
            )
        body: dict[str, Any] = {"transition": {"id": transition_id}}
        if comment:
            body["update"] = {"comment": [{"add": {"body": comment}}]}
        if resolution:
            body.setdefault("fields", {})["resolution"] = {"name": resolution}
        await client.post(f"/rest/api/2/issue/{issue_key}/transitions", json=body)
        return {
            "transitioned": True,
            "issue_key": issue_key,
            "transition_id": transition_id,
        }

    @mcp.tool
    async def get_issue_changelog(
        issue_key: str,
        start_at: int = 0,
        max_results: int = 100,
    ) -> dict:
        """Get the full change history for a Jira issue."""
        return await client.get(
            f"/rest/api/2/issue/{issue_key}/changelog",
            params={"startAt": start_at, "maxResults": max_results},
        )

    @mcp.tool
    async def watch_issue(issue_key: str, account_id: Optional[str] = None) -> dict:
        """Watch a Jira issue to receive email notifications.

        Watches as the current user if account_id is omitted.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "watch_issue is disabled: server is in read-only mode"
            )
        # Jira Server: POST with a JSON string body to watch as a specific user,
        # or POST with no body to watch as the current session user.
        # httpx treats json=None as no body, which is correct for self-watch.
        await client.post(
            f"/rest/api/2/issue/{issue_key}/watchers",
            json=account_id,  # None = no body = self-watch; string = watch as user
        )
        return {"watching": True, "issue_key": issue_key}

    @mcp.tool
    async def unwatch_issue(
        issue_key: str,
        account_id: Optional[str] = None,
    ) -> dict:
        """Remove a watcher from a Jira issue."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "unwatch_issue is disabled: server is in read-only mode"
            )
        params: dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        await client.delete(
            f"/rest/api/2/issue/{issue_key}/watchers",
            params=params or None,
        )
        return {"unwatched": True, "issue_key": issue_key}
