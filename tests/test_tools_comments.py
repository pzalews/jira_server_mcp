import pytest
import httpx
import respx
from fastmcp import FastMCP, Client
from jira_mcp.config import Settings
from jira_mcp.client import JiraClient
from jira_mcp.tools.comments import register_comments

JIRA_URL = "https://jira.test.example.com"


@pytest.fixture
def mcp_setup(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "test-token")
    settings = Settings()
    jira = JiraClient(settings)
    mcp = FastMCP("test")
    register_comments(mcp, jira, settings)
    return mcp, jira


@pytest.mark.asyncio
async def test_list_comments(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/comment").mock(
            return_value=httpx.Response(200, json={
                "comments": [{"id": "101", "body": "Hello"}], "total": 1,
            })
        )
        async with Client(mcp) as c:
            result = await c.call_tool("list_comments", {"issue_key": "PROJ-1"})
    assert result is not None


@pytest.mark.asyncio
async def test_add_comment(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue/PROJ-1/comment").mock(
            return_value=httpx.Response(201, json={"id": "102", "body": "Added"})
        )
        async with Client(mcp) as c:
            result = await c.call_tool("add_comment", {
                "issue_key": "PROJ-1", "body": "This is a comment",
            })
    assert result is not None


@pytest.mark.asyncio
async def test_update_comment(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.put("/rest/api/2/issue/PROJ-1/comment/102").mock(
            return_value=httpx.Response(200, json={"id": "102", "body": "Updated"})
        )
        async with Client(mcp) as c:
            result = await c.call_tool("update_comment", {
                "issue_key": "PROJ-1", "comment_id": "102", "body": "Updated text",
            })
    assert result is not None


@pytest.mark.asyncio
async def test_delete_comment(mcp_setup):
    mcp, _ = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.delete("/rest/api/2/issue/PROJ-1/comment/102").mock(
            return_value=httpx.Response(204)
        )
        async with Client(mcp) as c:
            result = await c.call_tool("delete_comment", {
                "issue_key": "PROJ-1", "comment_id": "102",
            })
    assert result is not None
