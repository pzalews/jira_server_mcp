import pytest
import httpx
import respx
from fastmcp import FastMCP, Client
from jira_mcp.config import Settings
from jira_mcp.client import JiraClient
from jira_mcp.tools.issues import register_issues
from jira_mcp.tools.comments import register_comments
from jira_mcp.tools.attachments import register_attachments
from jira_mcp.tools.agile import register_agile

JIRA_URL = "https://jira.test.example.com"


@pytest.fixture
def readonly_mcp(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_READ_ONLY", "true")
    settings = Settings()
    jira = JiraClient(settings)
    mcp = FastMCP("test")
    register_issues(mcp, jira, settings)
    register_comments(mcp, jira, settings)
    register_attachments(mcp, jira, settings)
    register_agile(mcp, jira, settings)
    return mcp


WRITE_TOOLS_AND_ARGS = [
    ("create_issue", {"project_key": "PROJ", "summary": "Test"}),
    ("update_issue", {"issue_key": "PROJ-1", "summary": "Updated"}),
    ("delete_issue", {"issue_key": "PROJ-1"}),
    ("assign_issue", {"issue_key": "PROJ-1", "assignee": "bob"}),
    ("transition_issue", {"issue_key": "PROJ-1", "transition_id": "31"}),
    ("link_issues", {"from_issue_key": "PROJ-1", "to_issue_key": "PROJ-2", "link_type": "blocks"}),
    ("watch_issue", {"issue_key": "PROJ-1"}),
    ("unwatch_issue", {"issue_key": "PROJ-1"}),
    ("add_comment", {"issue_key": "PROJ-1", "body": "hello"}),
    ("update_comment", {"issue_key": "PROJ-1", "comment_id": "1", "body": "updated"}),
    ("delete_comment", {"issue_key": "PROJ-1", "comment_id": "1"}),
    ("add_attachment", {"issue_key": "PROJ-1", "filename": "file.txt", "content_base64": "aGVsbG8="}),
    ("delete_attachment", {"attachment_id": "100"}),
    ("create_sprint", {"board_id": 1, "name": "Sprint X"}),
    ("start_sprint", {"sprint_id": 10}),
    ("close_sprint", {"sprint_id": 10}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name,args", WRITE_TOOLS_AND_ARGS)
async def test_write_tool_blocked_in_readonly(readonly_mcp, tool_name, args):
    """All write tools must return error content (not succeed) in read-only mode."""
    with respx.mock(base_url=JIRA_URL):
        # No HTTP mocks needed — read-only check fires before any HTTP call
        async with Client(readonly_mcp) as c:
            result = await c.call_tool(tool_name, args, raise_on_error=False)
    # FastMCP returns is_error=True when a tool raises an exception
    assert result.is_error, \
        f"Tool {tool_name!r} did not return error content in read-only mode. Got: {str(result)[:200]}"
    # Check error message text from the content list
    content_text = " ".join(
        block.text for block in result.content
        if hasattr(block, "text")
    ).lower()
    assert any(kw in content_text for kw in ["read-only", "disabled", "read_only"]), \
        f"Tool {tool_name!r} error did not mention read-only. Got: {content_text[:200]}"


@pytest.mark.asyncio
async def test_search_issues_allowed_in_readonly(readonly_mcp):
    """Read tools must work normally in read-only mode."""
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/search").mock(
            return_value=httpx.Response(200, json={
                "issues": [], "total": 0, "startAt": 0, "maxResults": 50
            })
        )
        async with Client(readonly_mcp) as c:
            result = await c.call_tool("search_issues", {"jql": "project=PROJ"})
    assert result is not None


@pytest.mark.asyncio
async def test_list_comments_allowed_in_readonly(readonly_mcp):
    """list_comments must work in read-only mode."""
    # Register comments on the readonly_mcp — it only has issues/comments/attachments/agile
    # But readonly_mcp already has register_comments since the fixture calls it
    # Wait — readonly_mcp fixture only registers issues, comments, attachments, agile
    # list_comments is in comments module which IS registered. Good.
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/comment").mock(
            return_value=httpx.Response(200, json={"comments": [], "total": 0})
        )
        async with Client(readonly_mcp) as c:
            result = await c.call_tool("list_comments", {"issue_key": "PROJ-1"})
    assert result is not None
