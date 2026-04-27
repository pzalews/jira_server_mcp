from __future__ import annotations
from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:

    @mcp.prompt
    def summarize_issue_prompt(issue_key: str) -> str:
        """Generate a prompt to create a structured summary of a Jira issue."""
        return (
            f"Summarize Jira issue **{issue_key}** by following these steps:\n\n"
            f"1. Call `get_issue('{issue_key}')` to fetch the full issue details\n"
            f"2. Call `list_comments('{issue_key}')` to retrieve all comments\n"
            f"3. Call `get_issue_changelog('{issue_key}')` to review the change history\n\n"
            "Produce a structured summary with these sections:\n\n"
            "### Status\n"
            "Current status, priority, and issue type\n\n"
            "### Owner\n"
            "Assignee and reporter with any relevant context\n\n"
            "### Description\n"
            "Concise restatement of the problem or objective\n\n"
            "### Recent Activity\n"
            "Last 5 meaningful changes from comments and changelog\n\n"
            "### Blockers\n"
            "Any blockers, dependencies, or risks mentioned\n\n"
            "### Next Steps\n"
            "Recommended 2-3 concrete actions based on current state\n"
        )

    @mcp.prompt
    def prepare_issue_update_prompt(issue_key: str) -> str:
        """Generate a prompt to draft a professional update comment for a Jira issue."""
        return (
            f"Prepare a professional progress update comment for Jira issue **{issue_key}**:\n\n"
            f"1. Call `get_issue('{issue_key}')` to read the current issue state\n"
            f"2. Call `list_comments('{issue_key}')` to review the most recent comments\n\n"
            "Draft a concise, professional comment that:\n"
            "- Summarizes current progress in 2-3 sentences\n"
            "- Calls out any blockers or risks\n"
            "- States the clear next action with owner and expected date\n"
            "- Uses professional language appropriate for a team update\n\n"
            "**Important:** Present the drafted comment for review. "
            "Do **not** call `add_comment` automatically — only post it "
            "if the user explicitly instructs you to do so.\n"
        )

    @mcp.prompt
    def triage_jql_results_prompt(jql: str) -> str:
        """Generate a prompt to triage and prioritize Jira issues from a JQL query."""
        return (
            f"Triage the Jira issues returned by: `{jql}`\n\n"
            f"1. Call `search_by_jql('{jql}', max_results=100)` to fetch the issues\n\n"
            "Analyze the results and produce a triage report:\n\n"
            "### By Priority\n"
            "Group issues: Critical → High → Medium → Low → None\n\n"
            "### By Status\n"
            "Group issues by their current workflow status\n\n"
            "### By Assignee\n"
            "Show workload distribution across team members\n\n"
            "### Blockers\n"
            "Issues that are explicitly blocking others or marked Critical/Blocker\n\n"
            "### Stale Issues\n"
            "Issues with no update in the last 7 days\n\n"
            "### Recommended Actions\n"
            "Top 3-5 issues requiring immediate attention, with reasoning\n"
        )
