from __future__ import annotations
from typing import Any, Optional
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.errors import JiraSoftwareUnavailableError, NotFoundError, ReadOnlyModeError


def register_agile(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    async def _agile_get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
        """GET wrapper that converts NotFoundError on agile paths to JiraSoftwareUnavailableError."""
        try:
            return await client.get(path, params=params)
        except NotFoundError as exc:
            raise JiraSoftwareUnavailableError(
                "Jira Software (Agile) APIs are not available on this instance. "
                "Ensure Jira Software is installed and the calling user has board access."
            ) from exc

    @mcp.tool
    async def list_boards(
        project_key: Optional[str] = None,
        board_type: Optional[str] = None,
        name: Optional[str] = None,
        max_results: int = 50,
    ) -> dict:
        """List Agile boards visible to the current user (Jira Software only).

        Args:
            project_key: Filter boards by project key.
            board_type: Filter by type: 'scrum' or 'kanban'.
            name: Filter by board name (partial match).
            max_results: Maximum boards to return.
        """
        params: dict[str, Any] = {"maxResults": max_results}
        if project_key:
            params["projectKeyOrId"] = project_key
        if board_type:
            params["type"] = board_type
        if name:
            params["name"] = name
        return await _agile_get("/rest/agile/1.0/board", params=params)

    @mcp.tool
    async def get_board(board_id: int) -> dict:
        """Get configuration and details for a specific Agile board."""
        return await _agile_get(f"/rest/agile/1.0/board/{board_id}")

    @mcp.tool
    async def list_sprints(
        board_id: int,
        state: Optional[str] = None,
        max_results: int = 50,
    ) -> dict:
        """List sprints for an Agile board (Jira Software only).

        Args:
            board_id: ID of the board.
            state: Filter by state: 'active', 'closed', 'future'.
        """
        params: dict[str, Any] = {"maxResults": max_results}
        if state:
            params["state"] = state
        return await _agile_get(
            f"/rest/agile/1.0/board/{board_id}/sprint", params=params
        )

    @mcp.tool
    async def get_sprint(sprint_id: int) -> dict:
        """Get details for a specific sprint."""
        return await _agile_get(f"/rest/agile/1.0/sprint/{sprint_id}")

    @mcp.tool
    async def list_issues_for_board(
        board_id: int,
        jql: Optional[str] = None,
        max_results: int = 50,
    ) -> dict:
        """List issues in the backlog and active sprint of an Agile board."""
        params: dict[str, Any] = {"maxResults": max_results}
        if jql:
            params["jql"] = jql
        return await _agile_get(
            f"/rest/agile/1.0/board/{board_id}/issue", params=params
        )

    @mcp.tool
    async def list_issues_for_sprint(sprint_id: int, max_results: int = 50) -> dict:
        """List all issues assigned to a specific sprint."""
        return await _agile_get(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            params={"maxResults": max_results},
        )

    @mcp.tool
    async def create_sprint(
        board_id: int,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: Optional[str] = None,
    ) -> dict:
        """Create a new sprint on an Agile board (Jira Software only).

        Args:
            board_id: ID of the board to create the sprint on.
            name: Sprint name.
            start_date: ISO 8601 start date (e.g., '2024-01-15T00:00:00.000+0000').
            end_date: ISO 8601 end date.
            goal: Sprint goal text.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "create_sprint is disabled: server is in read-only mode"
            )
        body: dict[str, Any] = {"name": name, "originBoardId": board_id}
        if start_date:
            body["startDate"] = start_date
        if end_date:
            body["endDate"] = end_date
        if goal:
            body["goal"] = goal
        try:
            return await client.post("/rest/agile/1.0/sprint", json=body)
        except NotFoundError as exc:
            raise JiraSoftwareUnavailableError(
                "Jira Software APIs not available on this instance"
            ) from exc

    @mcp.tool
    async def start_sprint(sprint_id: int) -> dict:
        """Start (activate) a sprint."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "start_sprint is disabled: server is in read-only mode"
            )
        try:
            await client.put(
                f"/rest/agile/1.0/sprint/{sprint_id}",
                json={"state": "active"},
            )
            return {"started": True, "sprint_id": sprint_id}
        except NotFoundError as exc:
            raise JiraSoftwareUnavailableError(
                "Jira Software APIs not available on this instance"
            ) from exc

    @mcp.tool
    async def close_sprint(sprint_id: int) -> dict:
        """Close (complete) a sprint."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "close_sprint is disabled: server is in read-only mode"
            )
        try:
            await client.put(
                f"/rest/agile/1.0/sprint/{sprint_id}",
                json={"state": "closed"},
            )
            return {"closed": True, "sprint_id": sprint_id}
        except NotFoundError as exc:
            raise JiraSoftwareUnavailableError(
                "Jira Software APIs not available on this instance"
            ) from exc
