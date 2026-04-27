from __future__ import annotations
import base64
import os
from fastmcp import FastMCP
from jira_mcp.client import JiraClient
from jira_mcp.config import Settings
from jira_mcp.errors import ReadOnlyModeError, ValidationError


def register_attachments(mcp: FastMCP, client: JiraClient, settings: Settings) -> None:

    @mcp.tool
    async def list_attachments(issue_key: str) -> list[dict]:
        """List all attachments on a Jira issue with metadata."""
        issue = await client.get(
            f"/rest/api/2/issue/{issue_key}",
            params={"fields": "attachment"},
        )
        return issue.get("fields", {}).get("attachment", [])

    @mcp.tool
    async def download_attachment_metadata(attachment_id: str) -> dict:
        """Get metadata for an attachment: filename, size, MIME type, and download URL.

        Note: Returns metadata only. The actual file content is available via the
        'content' URL in the response if the caller has network access to Jira.
        """
        return await client.get(f"/rest/api/2/attachment/{attachment_id}")

    @mcp.tool
    async def add_attachment(
        issue_key: str,
        filename: str,
        content_base64: str,
        mime_type: str = "application/octet-stream",
    ) -> list[dict]:
        """Upload a base64-encoded file as an attachment to a Jira issue.

        Args:
            issue_key: Target issue key.
            filename: Filename for the attachment (no path separators allowed).
            content_base64: Base64-encoded file content.
            mime_type: MIME type of the file.
        """
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "add_attachment is disabled: server is in read-only mode"
            )
        safe_name = os.path.basename(filename)
        if not safe_name or safe_name != filename or ".." in filename:
            raise ValidationError(
                f"Invalid filename {filename!r}: must not contain path separators or '..'"
            )
        try:
            content = base64.b64decode(content_base64)
        except Exception as exc:
            raise ValidationError(f"Invalid base64 content: {exc}") from exc

        files = {"file": (safe_name, content, mime_type)}
        result = await client.post(
            f"/rest/api/2/issue/{issue_key}/attachments",
            files=files,
        )
        return result if isinstance(result, list) else [result]

    @mcp.tool
    async def delete_attachment(attachment_id: str) -> dict:
        """Delete an attachment by its ID. Returns structured confirmation."""
        if settings.jira_read_only:
            raise ReadOnlyModeError(
                "delete_attachment is disabled: server is in read-only mode"
            )
        await client.delete(f"/rest/api/2/attachment/{attachment_id}")
        return {"deleted": True, "attachment_id": attachment_id}
