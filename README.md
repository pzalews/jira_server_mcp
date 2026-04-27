# Jira MCP Server

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for **Jira Server and Jira Data Center** (self-hosted). Built with [FastMCP](https://github.com/jlowin/fastmcp).

> **Not for Jira Cloud.** This server targets Jira Server / Data Center REST API v2.

## Features

- 43 MCP tools covering issues, comments, projects, attachments, users, JQL, workflows, and Agile boards/sprints
- 5 MCP resources for programmatic access to Jira data
- 3 reusable MCP prompts for common workflows
- PAT (Personal Access Token) and basic auth support
- Read-only mode to prevent accidental writes
- Structured JSON logging (never logs credentials)
- Custom header support for internal proxies and Zero Trust networks
- Docker deployment with non-root user
- Graceful degradation when Jira Software APIs are unavailable

## Supported Jira Versions

**Jira Server and Jira Data Center** — any version supporting REST API v2 (tested on 8.x and 9.x).

## Installation

### From source

```bash
git clone <repo>
cd jira_server_mcp
pip install -e .
```

### Requirements

- Python 3.12+
- Dependencies: `fastmcp`, `httpx`, `pydantic`, `pydantic-settings`, `tenacity`

## Configuration

All configuration via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|---|---|---|---|
| `JIRA_URL` | ✅ | — | Jira Server base URL (no trailing slash) |
| `JIRA_TOKEN` | — | — | Personal Access Token (preferred auth) |
| `JIRA_USERNAME` | — | — | Username for basic auth |
| `JIRA_PASSWORD` | — | — | Password for basic auth |
| `JIRA_DEFAULT_PROJECT` | — | — | Default project key |
| `JIRA_READ_ONLY` | — | `false` | Block all write operations |
| `JIRA_LOG_PATH` | — | — | Path to JSON log file (stderr always logged) |
| `JIRA_CUSTOM_HEADERS` | — | — | Comma-separated `KEY=VALUE` proxy headers |
| `MCP_TRANSPORT` | — | `stdio` | Transport: `stdio`, `http`, `streamable-http` |
| `MCP_HOST` | — | `0.0.0.0` | Host for HTTP transport |
| `MCP_PORT` | — | `8000` | Port for HTTP transport |

Copy `.env.example` to `.env` and fill in your values.

## Authentication

**PAT takes priority over username+password.**

### Personal Access Token (recommended)

Generate in Jira: Profile → Personal Access Tokens → Create token.

```env
JIRA_TOKEN=your-pat-here
```

Sent as:
```http
Authorization: Bearer <token>
```

### Basic Auth (fallback)

```env
JIRA_USERNAME=alice
JIRA_PASSWORD=secret
```

Sent as:
```http
Authorization: Basic base64(username:password)
```

**Credentials are never logged.**

## Read-Only Mode

Set `JIRA_READ_ONLY=true` to block all write operations. Useful for giving AI assistants read-only access.

**Blocked tools:** `create_issue`, `update_issue`, `delete_issue`, `assign_issue`, `transition_issue`, `link_issues`, `watch_issue`, `unwatch_issue`, `add_comment`, `update_comment`, `delete_comment`, `add_attachment`, `delete_attachment`, `create_sprint`, `start_sprint`, `close_sprint`

**Always available:** all search/read/list operations continue to work.

## Transport Modes

### stdio (default)

For MCP client integration (Claude Desktop, etc.):
```bash
JIRA_URL=https://jira.example.com JIRA_TOKEN=xxx jira-mcp
# or
python -m jira_mcp.app --transport stdio
```

### HTTP

For remote/shared access:
```bash
python -m jira_mcp.app --transport http --host 0.0.0.0 --port 8000
```

### Streamable HTTP

```bash
python -m jira_mcp.app --transport streamable-http --port 8000
```

## Docker Usage

```bash
# Build
docker build -t jira-mcp .

# Run with stdio transport (pipe to MCP client)
docker run -i --rm \
  -e JIRA_URL=https://jira.internal.example.com \
  -e JIRA_TOKEN=your-token \
  jira-mcp

# Run with HTTP transport
docker run -d -p 8000:8000 \
  -e JIRA_URL=https://jira.internal.example.com \
  -e JIRA_TOKEN=your-token \
  -e MCP_TRANSPORT=http \
  jira-mcp
```

The container runs as non-root user `jira` (UID 1001).

## docker-compose for Two Jira Servers

Create a `.env` with your tokens:
```bash
JIRA1_URL=https://jira1.internal.example.com
JIRA1_TOKEN=token-for-jira1
JIRA2_URL=https://jira2.internal.example.com
JIRA2_TOKEN=token-for-jira2
```

Then:
```bash
docker compose up -d
```

Each service is an independent MCP server for its own Jira instance.

## MCP Client Configuration

### Claude Desktop (stdio)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["-m", "jira_mcp.app"],
      "env": {
        "JIRA_URL": "https://jira.internal.example.com",
        "JIRA_TOKEN": "your-pat-here"
      }
    }
  }
}
```

### Two Jira servers in Claude Desktop

```json
{
  "mcpServers": {
    "jira-primary": {
      "command": "python",
      "args": ["-m", "jira_mcp.app"],
      "env": {
        "JIRA_URL": "https://jira1.internal.example.com",
        "JIRA_TOKEN": "token-for-jira1"
      }
    },
    "jira-secondary": {
      "command": "python",
      "args": ["-m", "jira_mcp.app"],
      "env": {
        "JIRA_URL": "https://jira2.internal.example.com",
        "JIRA_TOKEN": "token-for-jira2"
      }
    }
  }
}
```

### HTTP transport

```json
{
  "mcpServers": {
    "jira": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Tool Catalog

### Server / Metadata
| Tool | Description |
|---|---|
| `get_server_info` | Jira server version and build info |
| `get_myself` | Authenticated user profile |

### Projects
| Tool | Description |
|---|---|
| `list_projects` | All accessible projects |
| `get_project` | Project details by key |
| `get_project_versions` | Fix versions for a project |
| `get_project_components` | Components for a project |

### Issues
| Tool | Description |
|---|---|
| `search_issues` | Search issues using JQL |
| `get_issue` | Issue details by key |
| `create_issue` | Create a new issue *(write)* |
| `update_issue` | Update issue fields *(write)* |
| `delete_issue` | Delete an issue *(write)* |
| `assign_issue` | Assign or unassign an issue *(write)* |
| `link_issues` | Create issue link *(write)* |
| `get_issue_transitions` | List available transitions |
| `transition_issue` | Execute a workflow transition *(write)* |
| `get_issue_changelog` | Issue change history |
| `watch_issue` | Watch issue for notifications *(write)* |
| `unwatch_issue` | Remove watcher *(write)* |

### Comments
| Tool | Description |
|---|---|
| `list_comments` | List issue comments |
| `add_comment` | Add a comment *(write)* |
| `update_comment` | Update a comment *(write)* |
| `delete_comment` | Delete a comment *(write)* |

### Attachments
| Tool | Description |
|---|---|
| `list_attachments` | List issue attachments |
| `download_attachment_metadata` | Attachment metadata and URL |
| `add_attachment` | Upload base64-encoded file *(write)* |
| `delete_attachment` | Delete an attachment *(write)* |

### Users
| Tool | Description |
|---|---|
| `search_users` | Search users by name/email |
| `get_user` | User profile by account ID or username |

### JQL
| Tool | Description |
|---|---|
| `validate_jql` | Validate a JQL query |
| `search_by_jql` | Execute JQL, return structured results |

### Workflow / Fields
| Tool | Description |
|---|---|
| `list_issue_types` | All issue types |
| `list_fields` | All system and custom fields |
| `get_create_metadata` | Fields required to create issues |
| `get_edit_metadata` | Editable fields for an issue |
| `get_transition_metadata` | Transition fields (expanded) |

### Agile / Jira Software *(graceful error if unavailable)*
| Tool | Description |
|---|---|
| `list_boards` | Agile boards |
| `get_board` | Board details |
| `list_sprints` | Sprints for a board |
| `get_sprint` | Sprint details |
| `list_issues_for_board` | Issues on a board |
| `list_issues_for_sprint` | Issues in a sprint |
| `create_sprint` | Create a sprint *(write)* |
| `start_sprint` | Start a sprint *(write)* |
| `close_sprint` | Close a sprint *(write)* |

## Resources

| URI | Description |
|---|---|
| `jira://config/effective` | Current configuration (secrets redacted) |
| `jira://myself` | Authenticated user |
| `jira://projects` | All projects |
| `jira://issue/{issue_key}` | Issue by key |
| `jira://project/{project_key}` | Project by key |

## Prompts

| Prompt | Args | Description |
|---|---|---|
| `summarize_issue_prompt` | `issue_key` | Structured issue summary with status, blockers, next steps |
| `prepare_issue_update_prompt` | `issue_key` | Draft professional update comment (requires explicit approval to post) |
| `triage_jql_results_prompt` | `jql` | Group and prioritize issues from a JQL query |

## Security Notes

- **Credentials never logged** — auth headers and passwords are always redacted
- **Token-first auth** — PAT preferred; basic auth only as fallback
- **Read-only mode** — set `JIRA_READ_ONLY=true` for AI assistants without write access
- **Least-privilege tokens** — create project-scoped PATs with minimal permissions
- **Path traversal protection** — attachment filenames are validated against directory traversal
- **Non-root Docker** — container runs as UID 1001 (`jira` user)
- **Custom headers** — support for internal proxy / Zero Trust headers without logging values

## Development

```bash
# Run tests
python3 -m pytest tests/ -v

# Lint
python3 -m ruff check jira_mcp/

# Type check
python3 -m mypy jira_mcp/ --ignore-missing-imports
```

## Architecture

One MCP server instance = one Jira Server / Data Center instance. To connect to multiple Jira servers, run multiple MCP server processes (or containers) with separate environment variables.

```
jira_mcp/
├── app.py          # FastMCP server + main() entry point
├── config.py       # pydantic-settings configuration
├── client.py       # httpx async Jira REST client
├── models.py       # Pydantic input models
├── errors.py       # Exception hierarchy
├── logging_config.py # Structured JSON logging
├── tools/          # 43 MCP tools (6 modules)
├── resources/      # 5 MCP resources
└── prompts/        # 3 MCP prompts
```
# jira_server_mcp
