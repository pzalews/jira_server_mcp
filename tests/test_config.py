import base64
import pytest
from jira_mcp.config import Settings


def test_token_auth_header(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "my-token")
    s = Settings()
    assert s.auth_headers == {"Authorization": "Bearer my-token"}


def test_basic_auth_header(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_USERNAME", "user")
    monkeypatch.setenv("JIRA_PASSWORD", "pass")
    s = Settings()
    expected = base64.b64encode(b"user:pass").decode()
    assert s.auth_headers == {"Authorization": f"Basic {expected}"}


def test_token_takes_priority_over_basic(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "token123")
    monkeypatch.setenv("JIRA_USERNAME", "user")
    monkeypatch.setenv("JIRA_PASSWORD", "pass")
    s = Settings()
    assert s.auth_headers["Authorization"].startswith("Bearer token123")


def test_custom_headers_parsed(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "t")
    monkeypatch.setenv("JIRA_CUSTOM_HEADERS", "X-User=alice, X-Proxy=internal")
    s = Settings()
    assert s.custom_headers_dict == {"X-User": "alice", "X-Proxy": "internal"}


def test_trailing_slash_stripped(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com/")
    monkeypatch.setenv("JIRA_TOKEN", "t")
    s = Settings()
    assert s.jira_url == "https://jira.example.com"


def test_redacted_dict_hides_secrets(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "super-secret")
    monkeypatch.setenv("JIRA_PASSWORD", "also-secret")
    s = Settings()
    d = s.redacted_dict
    assert d["jira_token"] == "***"
    assert d["jira_password"] == "***"
    assert "super-secret" not in str(d)
    assert "also-secret" not in str(d)


def test_read_only_default_false(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "t")
    s = Settings()
    assert s.jira_read_only is False


def test_read_only_true(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "t")
    monkeypatch.setenv("JIRA_READ_ONLY", "true")
    s = Settings()
    assert s.jira_read_only is True


def test_no_auth_returns_empty(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    s = Settings()
    assert s.auth_headers == {}
