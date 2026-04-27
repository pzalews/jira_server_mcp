import pytest
import httpx
import respx
from jira_mcp.config import Settings
from jira_mcp.client import JiraClient
from jira_mcp.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    JiraApiError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

JIRA_URL = "https://jira.test.example.com"


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "test-token-abc")
    return Settings()


@pytest.fixture
def client(settings):
    return JiraClient(settings)


@pytest.mark.asyncio
async def test_get_sends_bearer_auth(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/serverInfo").mock(
            return_value=httpx.Response(200, json={"version": "8.22.0"})
        )
        result = await client.get("/rest/api/2/serverInfo")
        assert result["version"] == "8.22.0"
        assert mock.calls[0].request.headers["authorization"] == "Bearer test-token-abc"


@pytest.mark.asyncio
async def test_basic_auth_header(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_USERNAME", "alice")
    monkeypatch.setenv("JIRA_PASSWORD", "s3cret")
    c = JiraClient(Settings())
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/myself").mock(
            return_value=httpx.Response(200, json={"name": "alice"})
        )
        await c.get("/rest/api/2/myself")
        auth = mock.calls[0].request.headers["authorization"]
        assert auth.startswith("Basic ")


@pytest.mark.asyncio
async def test_custom_headers_forwarded(monkeypatch):
    monkeypatch.setenv("JIRA_URL", JIRA_URL)
    monkeypatch.setenv("JIRA_TOKEN", "t")
    monkeypatch.setenv("JIRA_CUSTOM_HEADERS", "X-Forwarded-User=bob")
    c = JiraClient(Settings())
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/myself").mock(
            return_value=httpx.Response(200, json={})
        )
        await c.get("/rest/api/2/myself")
        assert mock.calls[0].request.headers.get("x-forwarded-user") == "bob"


@pytest.mark.asyncio
async def test_401_raises_authentication_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/myself").mock(
            return_value=httpx.Response(401, json={"errorMessages": ["Not authenticated"]})
        )
        with pytest.raises(AuthenticationError):
            await client.get("/rest/api/2/myself")


@pytest.mark.asyncio
async def test_403_raises_authorization_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/project/SECRET").mock(
            return_value=httpx.Response(403, json={"errorMessages": ["Permission denied"]})
        )
        with pytest.raises(AuthorizationError):
            await client.get("/rest/api/2/project/SECRET")


@pytest.mark.asyncio
async def test_404_raises_not_found_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/issue/PROJ-999").mock(
            return_value=httpx.Response(404, json={"errorMessages": ["Issue does not exist"]})
        )
        with pytest.raises(NotFoundError):
            await client.get("/rest/api/2/issue/PROJ-999")


@pytest.mark.asyncio
async def test_409_raises_conflict_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue").mock(
            return_value=httpx.Response(409, json={"errorMessages": ["Conflict"]})
        )
        with pytest.raises(ConflictError):
            await client.post("/rest/api/2/issue", json={})


@pytest.mark.asyncio
async def test_429_raises_rate_limit_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/api/2/search").mock(
            return_value=httpx.Response(429, json={"errorMessages": ["Too many requests"]})
        )
        with pytest.raises(RateLimitError):
            await client.get("/rest/api/2/search")


@pytest.mark.asyncio
async def test_400_raises_validation_error(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue").mock(
            return_value=httpx.Response(400, json={"errors": {"summary": "Field required"}})
        )
        with pytest.raises(ValidationError):
            await client.post("/rest/api/2/issue", json={})


@pytest.mark.asyncio
async def test_post_returns_json(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.post("/rest/api/2/issue").mock(
            return_value=httpx.Response(201, json={"id": "10001", "key": "PROJ-1"})
        )
        result = await client.post("/rest/api/2/issue", json={"fields": {}})
        assert result["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_delete_no_content(client):
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.delete("/rest/api/2/issue/PROJ-1").mock(
            return_value=httpx.Response(204)
        )
        result = await client.delete("/rest/api/2/issue/PROJ-1")
        assert result is None


@pytest.mark.asyncio
async def test_paginate_collects_all_pages(client):
    page1 = {"values": [{"id": "1"}, {"id": "2"}], "startAt": 0, "maxResults": 2, "total": 4}
    page2 = {"values": [{"id": "3"}, {"id": "4"}], "startAt": 2, "maxResults": 2, "total": 4}
    with respx.mock(base_url=JIRA_URL) as mock:
        mock.get("/rest/agile/1.0/board").mock(side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ])
        results = await client.paginate("/rest/agile/1.0/board", page_size=2)
    assert len(results) == 4
    assert results[0]["id"] == "1"
    assert results[3]["id"] == "4"
