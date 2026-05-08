import pytest
import httpx
import respx
from fastmcp import FastMCP, Client
from jira_mcp.config import Settings
from jira_mcp.client import JiraClient
from jira_mcp.tools.issues import register_issues

JIRA_URL = "https://jira.test.example.com"


@pytest.fixture
def mcp_setup(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "test-token")
    settings = Settings()
    jira = JiraClient(settings)
    mcp = FastMCP("test")
    register_issues(mcp, jira, settings)
    return mcp, jira


@pytest.mark.asyncio
async def test_search_issues_tool(mcp_setup):
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/search").mock(
            return_value=httpx.Response(200, json={
                "issues": [{"key": "PROJ-1", "fields": {"summary": "Bug"}}],
                "total": 1, "startAt": 0, "maxResults": 50,
            })
        )
        async with Client(mcp) as c:
            result = await c.call_tool("search_issues", {"jql": "project=PROJ"})
    assert result is not None


@pytest.mark.asyncio
async def test_create_issue_calls_api(mcp_setup):
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue").mock(
            return_value=httpx.Response(201, json={"id": "10001", "key": "PROJ-1"})
        )
        async with Client(mcp) as c:
            result = await c.call_tool("create_issue", {
                "project_key": "PROJ",
                "summary": "Test issue",
            })
    assert result is not None


@pytest.mark.asyncio
async def test_delete_issue_returns_confirmation(mcp_setup):
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.delete("/rest/api/2/issue/PROJ-1").mock(
            return_value=httpx.Response(204)
        )
        async with Client(mcp) as c:
            result = await c.call_tool("delete_issue", {"issue_key": "PROJ-1"})
    assert result is not None


@pytest.mark.asyncio
async def test_transition_issue(mcp_setup):
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(204)
        )
        async with Client(mcp) as c:
            result = await c.call_tool("transition_issue", {
                "issue_key": "PROJ-1",
                "transition_id": "31",
            })
    assert result is not None


@pytest.mark.asyncio
async def test_get_issue_changelog(mcp_setup):
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/changelog").mock(
            return_value=httpx.Response(200, json={"values": [], "total": 0})
        )
        async with Client(mcp) as c:
            result = await c.call_tool("get_issue_changelog", {"issue_key": "PROJ-1"})
    assert result is not None


@pytest.mark.asyncio
async def test_create_issue_with_custom_fields(mcp_setup):
    mcp, jira = mcp_setup
    captured = {}
    with respx.mock(base_url=JIRA_URL) as mock:
        def capture(request):
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(201, json={"id": "10001", "key": "PROJ-1"})
        mock.post("/rest/api/2/issue").mock(side_effect=capture)
        async with Client(mcp) as c:
            await c.call_tool("create_issue", {
                "project_key": "PROJ",
                "summary": "Test with custom fields",
                "custom_fields": {
                    "customfield_10401": {"id": "15872"},
                    "customfield_10605": "Piotr Zalewski",
                },
            })
    fields = captured["body"]["fields"]
    assert fields["customfield_10401"] == {"id": "15872"}
    assert fields["customfield_10605"] == "Piotr Zalewski"


@pytest.mark.asyncio
async def test_update_issue_with_custom_fields(mcp_setup):
    mcp, jira = mcp_setup
    captured = {}
    with respx.mock(base_url=JIRA_URL) as mock:
        def capture(request):
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(204)
        mock.put("/rest/api/2/issue/PROJ-1").mock(side_effect=capture)
        async with Client(mcp) as c:
            result = await c.call_tool("update_issue", {
                "issue_key": "PROJ-1",
                "summary": "Updated summary",
                "custom_fields": {
                    "customfield_10603": {"id": "10505"},
                    "customfield_10602": {"id": "10500"},
                },
            })
    fields = captured["body"]["fields"]
    assert fields["summary"] == "Updated summary"
    assert fields["customfield_10603"] == {"id": "10505"}
    assert fields["customfield_10602"] == {"id": "10500"}


@pytest.mark.asyncio
async def test_update_issue_only_custom_fields(mcp_setup):
    """custom_fields alone should not raise ValidationError."""
    mcp, jira = mcp_setup
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.put("/rest/api/2/issue/PROJ-1").mock(return_value=httpx.Response(204))
        async with Client(mcp) as c:
            result = await c.call_tool("update_issue", {
                "issue_key": "PROJ-1",
                "custom_fields": {"customfield_10401": {"id": "15872"}},
            })
    assert result is not None
