from __future__ import annotations
import argparse
import logging

from fastmcp import FastMCP

from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.logging_config import setup_logging, host_only

logger = logging.getLogger("jira_mcp.app")


def build_server() -> tuple[FastMCP, Settings]:
    """Create and configure the FastMCP server. Called by main() and tests."""
    settings = Settings()
    setup_logging(settings.jira_log_path)

    client = JiraClient(settings)

    mcp = FastMCP(
        "Jira MCP Server",
        instructions=(
            "Production MCP server for Jira Server / Data Center. "
            "Provides tools for issue management, projects, comments, "
            "attachments, agile boards/sprints, JQL, and workflow transitions. "
            f"Read-only mode: {settings.jira_read_only}."
        ),
    )

    # Register all components (imports here to avoid circular deps)
    from jira_mcp.tools.issues import register_issues
    from jira_mcp.tools.comments import register_comments
    from jira_mcp.tools.projects import register_projects
    from jira_mcp.tools.users import register_users
    from jira_mcp.tools.workflows import register_workflows
    from jira_mcp.tools.attachments import register_attachments
    from jira_mcp.tools.agile import register_agile
    from jira_mcp.resources import register_resources
    from jira_mcp.prompts import register_prompts

    register_projects(mcp, client, settings)
    register_issues(mcp, client, settings)
    register_comments(mcp, client, settings)
    register_users(mcp, client, settings)
    register_workflows(mcp, client, settings)
    register_attachments(mcp, client, settings)
    register_agile(mcp, client, settings)
    register_resources(mcp, client, settings)
    register_prompts(mcp)

    logger.info(
        "server_initialized",
        extra={"extra": {
            "jira_host": host_only(settings.jira_url),
            "read_only": settings.jira_read_only,
            "transport": settings.mcp_transport,
        }},
    )
    return mcp, settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Jira MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http"],
        default=None,
        help="MCP transport (overrides MCP_TRANSPORT env var)",
    )
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    mcp, settings = build_server()

    transport = args.transport or settings.mcp_transport
    host = args.host or settings.mcp_host
    port = args.port or settings.mcp_port

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
