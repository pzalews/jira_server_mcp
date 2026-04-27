import pytest
import httpx
import respx
from fastmcp import FastMCP, Client
from jira_mcp.config import Settings
from jira_mcp.client import JiraClient
from jira_mcp.tools.agile import register_agile

JIRA_URL = "https://jira.test.example.com"


@pytest.fixture
def mcp_setup(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "test-token")
    settings = Settings()
    jira = JiraClient(settings)
    mcp = FastMCP("test")
    register_agile(mcp, jira, settings)
    return mcp, jira


@pytest.mark.asyncio
async def test_list_boards_returns_data(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/agile/1.0/board").mock(
            return_value=httpx.Response(200, json={
                "values": [{"id": 1, "name": "PROJ board"}],
                "total": 1, "startAt": 0, "maxResults": 50,
            })
        )
        async with Client(mcp) as c:
            result = await c.call_tool("list_boards", {})
    assert result is not None


@pytest.mark.asyncio
async def test_list_boards_software_unavailable(mcp_setup):
    """When Jira Software is not installed, 404 on agile endpoint returns error content."""
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/agile/1.0/board").mock(
            return_value=httpx.Response(404, json={"errorMessages": ["No board found"]})
        )
        # FastMCP converts tool exceptions to error content; result is not None
        async with Client(mcp) as c:
            result = await c.call_tool("list_boards", {}, raise_on_error=False)
    # Result should contain error info (not raise unhandled exception)
    assert result is not None
    assert result.is_error


@pytest.mark.asyncio
async def test_list_sprints(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/agile/1.0/board/1/sprint").mock(
            return_value=httpx.Response(200, json={
                "values": [{"id": 10, "name": "Sprint 1", "state": "active"}],
                "total": 1, "startAt": 0, "maxResults": 50,
            })
        )
        async with Client(mcp) as c:
            result = await c.call_tool("list_sprints", {"board_id": 1})
    assert result is not None


@pytest.mark.asyncio
async def test_agile_unavailable_on_sprint_endpoint(mcp_setup):
    """404 on sprint endpoint converts to JiraSoftwareUnavailableError (returned as error content)."""
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/agile/1.0/board/99/sprint").mock(
            return_value=httpx.Response(404, json={"errorMessages": ["Board not found"]})
        )
        async with Client(mcp) as c:
            result = await c.call_tool("list_sprints", {"board_id": 99}, raise_on_error=False)
    assert result is not None
    assert result.is_error
